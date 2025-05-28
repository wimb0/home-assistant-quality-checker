# linkplay: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule mandates that common Home Assistant patterns, such as data update coordinators and base entities, be placed in standardized module files (`coordinator.py` and `entity.py`, respectively) to enhance consistency and maintainability across integrations.

This rule applies to the `linkplay` integration because:
1.  It provides multiple entity platforms (`media_player`, `button`), making a base entity class beneficial for code reuse.
2.  It involves polling for device state updates, a pattern typically managed by a `DataUpdateCoordinator`.

The `linkplay` integration partially follows this rule:

*   **Base Entity (`entity.py`):** The integration correctly implements a base entity, `LinkPlayBaseEntity`, within the `entity.py` file. This base class is used by `LinkPlayButton` (in `button.py`) and `LinkPlayMediaPlayerEntity` (in `media_player.py`), adhering to this aspect of the rule.

*   **Coordinator (`coordinator.py`):** The integration does not use a `DataUpdateCoordinator` to manage data fetching, despite its `media_player` entities performing polling. In `media_player.py`, the `LinkPlayMediaPlayerEntity` class has its own `async_update` method and `SCAN_INTERVAL`, indicating per-entity polling:
    ```python
    # media_player.py
    SCAN_INTERVAL = timedelta(seconds=5)
    # ...
    class LinkPlayMediaPlayerEntity(LinkPlayBaseEntity, MediaPlayerEntity):
        # ...
        async def async_update(self) -> None:
            """Update the state of the media player."""
            try:
                await self._bridge.player.update_status()
                self._retry_count = 0
                self._update_properties()
            except LinkPlayRequestException:
                # ...
    ```
    The common pattern for such polling is to use a `DataUpdateCoordinator` defined in `coordinator.py` to centralize data fetching and updates. The absence of this pattern means this part of the rule is not met.

Because the integration does not centralize its data polling for media player entities using a `DataUpdateCoordinator` in `coordinator.py`, it does not fully comply with the `common-modules` rule.

## Suggestions

To fully comply with the `common-modules` rule, the `linkplay` integration should implement a `DataUpdateCoordinator` for managing the state updates of its media player entities.

1.  **Create `coordinator.py`:**
    Add a new file named `coordinator.py` to the `linkplay` integration directory.

2.  **Define the Coordinator:**
    In `coordinator.py`, define a coordinator class that inherits from `DataUpdateCoordinator`. This coordinator will be responsible for fetching the status from the LinkPlay device.

    ```python
    # linkplay/coordinator.py
    import logging
    from datetime import timedelta

    from linkplay.bridge import LinkPlayBridge
    from linkplay.exceptions import LinkPlayRequestException # Assuming LinkPlayStatusData is the type of data fetched

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

    from .const import DOMAIN # You might need to adjust imports

    _LOGGER = logging.getLogger(__name__)

    class LinkPlayDataUpdateCoordinator(DataUpdateCoordinator[None]): # Or a specific data type if status returns structured data
        """Class to manage fetching LinkPlay device data."""

        def __init__(self, hass: HomeAssistant, bridge: LinkPlayBridge, host: str) -> None:
            """Initialize coordinator."""
            self.bridge = bridge
            super().__init__(
                hass,
                _LOGGER,
                name=f"{DOMAIN} {host}",
                update_interval=timedelta(seconds=10), # Or use SCAN_INTERVAL from media_player.py
            )

        async def _async_update_data(self) -> None: # Or return type if not None
            """Fetch data from API endpoint."""
            try:
                # This is the core data fetching logic, previously in LinkPlayMediaPlayerEntity.async_update
                await self.bridge.player.update_status()
                # If update_status returns data, you'd return it here.
                # For now, assuming it updates the bridge.player object in place.
                return None # Or the fetched data
            except LinkPlayRequestException as err:
                raise UpdateFailed(f"Error communicating with API: {err}") from err
    ```

3.  **Integrate Coordinator in `__init__.py`:**
    Instantiate and store the coordinator in `__init__.py` during setup. This typically involves associating a coordinator instance with each configured device (bridge).

    ```python
    # linkplay/__init__.py
    # ... (other imports)
    from .coordinator import LinkPlayDataUpdateCoordinator

    @dataclass
    class LinkPlayData:
        """Data for LinkPlay."""
        bridge: LinkPlayBridge
        coordinator: LinkPlayDataUpdateCoordinator # Add coordinator here

    # ...

    async def async_setup_entry(hass: HomeAssistant, entry: LinkPlayConfigEntry) -> bool:
        """Async setup hass config entry. Called when an entry has been setup."""
        # ... (session and bridge setup) ...

        coordinator = LinkPlayDataUpdateCoordinator(hass, bridge, entry.data[CONF_HOST])
        await coordinator.async_config_entry_first_refresh() # Perform initial refresh

        # ... (controller setup) ...

        entry.runtime_data = LinkPlayData(bridge=bridge, coordinator=coordinator) # Store coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    ```
    Ensure `LinkPlayConfigEntry` type hint is updated if `LinkPlayData` changes.

4.  **Refactor `media_player.py`:**
    Modify `LinkPlayMediaPlayerEntity` to inherit from `CoordinatorEntity` and use the coordinator for data and updates. Remove the `async_update` method and `SCAN_INTERVAL` from the entity.

    ```python
    # linkplay/media_player.py
    # ...
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
    # ...
    # from . import LinkPlayConfigEntry # Already there
    from .coordinator import LinkPlayDataUpdateCoordinator # Import the coordinator

    # Remove: SCAN_INTERVAL = timedelta(seconds=5)
    # Remove: PARALLEL_UPDATES = 1 (Coordinator handles this)

    # ...

    class LinkPlayMediaPlayerEntity(LinkPlayBaseEntity, CoordinatorEntity[LinkPlayDataUpdateCoordinator], MediaPlayerEntity):
        """Representation of a LinkPlay media player."""

        # ... (attributes like _attr_device_class, etc.)

        def __init__(self, bridge: LinkPlayBridge, coordinator: LinkPlayDataUpdateCoordinator) -> None:
            """Initialize the LinkPlay media player."""
            super().__init__(bridge) # Call LinkPlayBaseEntity's init
            CoordinatorEntity.__init__(self, coordinator) # Call CoordinatorEntity's init
            self._attr_unique_id = bridge.device.uuid
            # self._retry_count can likely be removed as coordinator handles retries/availability

            # Initial setup of source_list, sound_mode_list can remain if static
            # or be moved to _handle_coordinator_update if derived from coordinator data.
            self._update_properties_from_bridge() # Perform initial property update

        # Remove async_update method entirely

        @callback
        def _handle_coordinator_update(self) -> None:
            """Handle updated data from the coordinator."""
            # This method is called by the CoordinatorEntity when the coordinator has new data.
            # Update entity properties based on self.coordinator.data or self._bridge.player
            # (since the coordinator updates self.bridge.player)
            self._update_properties_from_bridge()
            self.async_write_ha_state()

        def _update_properties_from_bridge(self) -> None:
            """Update the properties of the media player from the bridge object."""
            # This is the logic from the old _update_properties, now using self._bridge
            # (which is updated by the coordinator)
            # Ensure self._bridge is the one associated with this entity/coordinator
            player_status = self._bridge.player.status # Access data via self._bridge.player
            
            self._attr_available = True # CoordinatorEntity handles availability based on coordinator success
            self._attr_state = STATE_MAP[player_status]
            # ... (rest of the property updates using self._bridge.player) ...

        @property
        def available(self) -> bool:
            """Return if entity is available."""
            # The coordinator handles update success. If the coordinator failed last update,
            # CoordinatorEntity marks it unavailable.
            # If bridge can become unavailable independently, add specific checks.
            return super().available and self._bridge is not None # And potentially other bridge checks

        # ... (other methods like async_select_source, async_set_volume_level, etc.)
        # These methods will continue to use self._bridge.player.some_method() to send commands.
        # The state will then be refreshed by the coordinator in the next update cycle.
    ```
    In `async_setup_entry` for `media_player.py`:
    ```python
    # linkplay/media_player.py
    async def async_setup_entry(
        hass: HomeAssistant,
        entry: LinkPlayConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up a media player from a config entry."""
        # ... (platform registration) ...
        bridge = entry.runtime_data.bridge
        coordinator = entry.runtime_data.coordinator
        async_add_entities([LinkPlayMediaPlayerEntity(bridge, coordinator)])
    ```

By making these changes, the `linkplay` integration will centralize its data polling mechanism, aligning with Home Assistant's common patterns and fully satisfying the `common-modules` rule. This typically leads to more efficient updates, better error handling, and improved consistency.

_Created at 2025-05-11 07:09:05. Prompt tokens: 10419, Output tokens: 2400, Total tokens: 15181_
