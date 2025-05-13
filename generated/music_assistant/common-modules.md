# music_assistant: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule requires that common patterns like coordinators and base entities are placed in standardized module names (`coordinator.py` and `entity.py`, respectively) to improve consistency and maintainability across Home Assistant integrations.

This rule applies to the `music_assistant` integration as it provides entities and has a central mechanism for managing communication and data updates with the Music Assistant server.

The integration's compliance with the rule is as follows:

1.  **Base Entity (`entity.py`):**
    *   The integration defines a base entity class `MusicAssistantEntity` in `homeassistant/components/music_assistant/entity.py`.
    *   This base entity is then inherited by specific platform entities, such as `MusicAssistantPlayer` in `homeassistant/components/music_assistant/media_player.py`.
    *   **This part of the rule is correctly followed.**

    ```python
    # homeassistant/components/music_assistant/entity.py
    class MusicAssistantEntity(Entity):
        # ...
        pass

    # homeassistant/components/music_assistant/media_player.py
    class MusicAssistantPlayer(MusicAssistantEntity, MediaPlayerEntity):
        # ...
        pass
    ```

2.  **Coordinator (`coordinator.py`):**
    *   The rule states that "the coordinator should be placed in `coordinator.py`," with `DataUpdateCoordinator` given as a common example for centralizing data fetching.
    *   The `music_assistant` integration does not use `DataUpdateCoordinator`. Instead, it relies on the `MusicAssistantClient` (from the `music-assistant-client` library) which maintains a persistent connection to the Music Assistant server and receives updates via an event-driven mechanism.
    *   The setup, management of this client, and its listener task (`_client_listen` function) are currently handled within `homeassistant/components/music_assistant/__init__.py`. This client and its associated logic act as the central "coordinator" for data and updates from the Music Assistant server.
    *   There is no `coordinator.py` file in the integration. The logic that serves the purpose of a coordinator (managing the `MusicAssistantClient`, its connection, and the event listener task) is located in `__init__.py`.
    *   **This part of the rule is not followed.** The central data/event management logic should be moved to a `coordinator.py` file to align with the rule's intent for consistency and findability, even if it's not a `DataUpdateCoordinator` subclass.

    Relevant code in `homeassistant/components/music_assistant/__init__.py`:
    ```python
    @dataclass
    class MusicAssistantEntryData:
        """Hold Mass data for the config entry."""

        mass: MusicAssistantClient
        listen_task: asyncio.Task

    async def async_setup_entry(
        hass: HomeAssistant, entry: MusicAssistantConfigEntry
    ) -> bool:
        # ...
        mass = MusicAssistantClient(mass_url, http_session)
        # ... connection logic ...
        listen_task = asyncio.create_task(_client_listen(hass, entry, mass, init_ready))
        # ...
        entry.runtime_data = MusicAssistantEntryData(mass, listen_task)
        # ...
        return True

    async def _client_listen(
        hass: HomeAssistant,
        entry: ConfigEntry,
        mass: MusicAssistantClient,
        init_ready: asyncio.Event,
    ) -> None:
        # ... client listening logic ...
        pass
    ```

Since the base entity is correctly placed but the coordinator-equivalent logic is not in `coordinator.py`, the integration does not fully follow the `common-modules` rule.

## Suggestions

To make the `music_assistant` integration compliant with the `common-modules` rule, the central client management and listening logic should be moved from `__init__.py` to a new `coordinator.py` file.

1.  **Create `homeassistant/components/music_assistant/coordinator.py`**.
2.  **Define a coordinator class** in this new file (e.g., `MusicAssistantCoordinator`). This class would encapsulate:
    *   The `MusicAssistantClient` instance (`mass`).
    *   The listener task (`listen_task`).
    *   Methods for initialization (connecting the client, starting the listener).
    *   Methods for shutdown (disconnecting the client, canceling the task).
    *   The logic currently in `_client_listen` from `__init__.py`.
    *   The `MusicAssistantEntryData` dataclass could be merged into this coordinator class or the coordinator class itself could be stored in `entry.runtime_data`.

    **Example `coordinator.py` structure:**
    ```python
    # homeassistant/components/music_assistant/coordinator.py
    import asyncio
    from music_assistant_client import MusicAssistantClient
    # ... other necessary imports from __init__.py and Home Assistant ...

    from homeassistant.config_entries import ConfigEntry, ConfigEntryState
    from homeassistant.const import CONF_URL, EVENT_HOMEASSISTANT_STOP
    from homeassistant.core import Event, HomeAssistant
    from homeassistant.exceptions import ConfigEntryNotReady
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .const import DOMAIN, LOGGER # Assuming CONNECT_TIMEOUT, LISTEN_READY_TIMEOUT are here or defined

    CONNECT_TIMEOUT = 10  # Define or import appropriately
    LISTEN_READY_TIMEOUT = 30 # Define or import appropriately


    class MusicAssistantCoordinator:
        """Manages the Music Assistant client and data."""

        def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
            """Initialize the coordinator."""
            self.hass = hass
            self.entry = entry
            self.mass_url = entry.data[CONF_URL]
            self._http_session = async_get_clientsession(hass, verify_ssl=False)
            self.mass = MusicAssistantClient(self.mass_url, self._http_session)
            self.listen_task: asyncio.Task | None = None
            self._init_ready = asyncio.Event()
            self._hass_stop_listener = None

        async def async_initialize_client(self) -> None:
            """Connect to Music Assistant and start listening for events."""
            try:
                async with asyncio.timeout(CONNECT_TIMEOUT):
                    await self.mass.connect()
            except (TimeoutError, CannotConnect) as err:
                raise ConfigEntryNotReady(
                    f"Failed to connect to music assistant server {self.mass_url}"
                ) from err
            # ... (Include other exception handling from __init__.py's async_setup_entry for connection)

            # Start listener task
            self.listen_task = self.hass.async_create_task(self._client_listen_loop())

            try:
                async with asyncio.timeout(LISTEN_READY_TIMEOUT):
                    await self._init_ready.wait()
            except TimeoutError as err:
                if self.listen_task:
                    self.listen_task.cancel()
                raise ConfigEntryNotReady("Music Assistant client not ready") from err

            if self.listen_task.done() and (listen_error := self.listen_task.exception()):
                await self.async_shutdown_client() # Ensure client is cleaned up
                raise ConfigEntryNotReady(f"Listener task failed during startup: {listen_error}") from listen_error
            
            self._hass_stop_listener = self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STOP, self._on_hass_stop
            )


        async def _client_listen_loop(self) -> None:
            """Listen with the client."""
            try:
                await self.mass.start_listening(self._init_ready)
            except MusicAssistantError as err:
                if self.entry.state != ConfigEntryState.LOADED:
                    raise
                LOGGER.error("Failed to listen: %s", err)
            except Exception as err:  # pylint: disable=broad-except
                if self.entry.state != ConfigEntryState.LOADED:
                    raise
                LOGGER.exception("Unexpected exception: %s", err)

            if not self.hass.is_stopping and self.entry.state == ConfigEntryState.LOADED:
                LOGGER.debug("Disconnected from server. Reloading integration")
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self.entry.entry_id)
                )
        
        async def _on_hass_stop(self, event: Event) -> None:
            """Handle Home Assistant stop event."""
            await self.mass.disconnect()

        async def async_shutdown_client(self) -> None:
            """Stop the client and cancel listener task."""
            if self._hass_stop_listener:
                self._hass_stop_listener()
                self._hass_stop_listener = None
            if self.listen_task:
                self.listen_task.cancel()
                try:
                    await self.listen_task
                except asyncio.CancelledError:
                    pass # Expected
            if self.mass.connected:
                await self.mass.disconnect()

    ```

3.  **Update `__init__.py`**:
    *   Import the new `MusicAssistantCoordinator`.
    *   In `async_setup_entry`, instantiate the coordinator, call its initialization method, and store the coordinator instance in `entry.runtime_data`.
    *   In `async_unload_entry`, retrieve the coordinator from `entry.runtime_data` and call its shutdown method.
    *   The `MusicAssistantEntryData` dataclass can be removed if the coordinator itself is stored.

    **Example `__init__.py` changes:**
    ```python
    # homeassistant/components/music_assistant/__init__.py
    from .coordinator import MusicAssistantCoordinator # Add this import

    # Remove MusicAssistantEntryData if coordinator instance is stored directly

    async def async_setup_entry(
        hass: HomeAssistant, entry: MusicAssistantConfigEntry
    ) -> bool:
        coordinator = MusicAssistantCoordinator(hass, entry)
        await coordinator.async_initialize_client() # This will raise ConfigEntryNotReady on failure
        
        entry.runtime_data = coordinator # Store coordinator instance

        # ... (rest of setup_entry, e.g., platform forwarding)
        # Make sure to handle player removal logic by accessing coordinator.mass
        
        return True

    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        if unload_ok:
            coordinator: MusicAssistantCoordinator = entry.runtime_data
            await coordinator.async_shutdown_client()
            entry.runtime_data = None # Clear runtime_data

        return unload_ok
    ```

4.  **Update Entities and Services**:
    *   Entities (like `MusicAssistantEntity` and `MusicAssistantPlayer`) would now be initialized with the `MusicAssistantCoordinator` instance (or access `coordinator.mass` if the coordinator is stored in `hass.data`).
    *   The `get_music_assistant_client` helper in `actions.py` would need to be updated to retrieve the `mass` client from `entry.runtime_data.mass` (if `entry.runtime_data` is the coordinator instance).
    ```python
    # homeassistant/components/music_assistant/entity.py
    # ...
    # if coordinator is passed to entity init:
    # def __init__(self, coordinator: MusicAssistantCoordinator, player_id: str) -> None:
    #    self.coordinator = coordinator
    #    self.mass = coordinator.mass
    # ...
    # or if coordinator is hass.data[DOMAIN][entry.entry_id].coordinator:
    # self.mass = self.coordinator.mass
    ```

These changes would centralize the client management logic into `coordinator.py`, making the integration's structure more consistent with Home Assistant best practices and satisfying the `common-modules` rule.

_Created at 2025-05-13 10:00:05. Prompt tokens: 30029, Output tokens: 2891, Total tokens: 37489_
