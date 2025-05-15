# open_epaper_link: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule applies to the `open_epaper_link` integration. The integration's `Hub` class instance is a clear example of runtime data: it manages the WebSocket connection, stores tag states, AP status, and other information that is essential for the integration's operation during the lifetime of its configuration entry, but is not persisted to YAML or storage.

The integration currently does **NOT** follow this rule.
Instead of using `ConfigEntry.runtime_data` to store the `Hub` instance, it uses the older pattern of storing it in `hass.data`.

Specifically, in `homeassistant/components/open_epaper_link/__init__.py`:
1.  A `Hub` instance is created: `hub = Hub(hass, entry)`.
2.  This instance is stored in `hass.data`: `hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub`.
3.  Throughout the integration (e.g., in platform setup files like `sensor.py`, `switch.py`, and in `async_update_options`, `async_unload_entry` within `__init__.py`), the `Hub` instance is retrieved from `hass.data[DOMAIN][entry.entry_id]`.
4.  The `ConfigEntry` type hint in `async_setup_entry` and other functions is the generic `ConfigEntry`, not a specialized `ConfigEntry[Hub]` type as recommended by the rule for better type safety and clarity.

Using `entry.runtime_data` provides a standardized, type-safe way to manage such runtime objects, directly associating them with their respective config entry.

## Suggestions

To make the `open_epaper_link` integration compliant with the `runtime-data` rule, the following changes are recommended:

1.  **Modify `__init__.py`:**
    *   Import the `Hub` class and `ConfigEntry` type.
    *   Define a type alias for a `ConfigEntry` that holds a `Hub` instance in its `runtime_data`.
    *   Store the `Hub` instance in `entry.runtime_data`.
    *   Update functions that access the hub to retrieve it from `entry.runtime_data`.
    *   Pass the `hub` instance to `async_setup_services`.

    ```python
    # homeassistant/components/open_epaper_link/__init__.py
    # ...
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from .const import DOMAIN
    from .hub import Hub # Import Hub
    from .services import async_setup_services, async_unload_services
    # ...

    # Define a typed ConfigEntry
    OpenEPaperLinkConfigEntry = ConfigEntry[Hub]

    # ...
    async def async_setup_entry(hass: HomeAssistant, entry: OpenEPaperLinkConfigEntry) -> bool: # Use typed ConfigEntry
        """Set up OpenEPaperLink integration from a config entry."""
        hub = Hub(hass, entry)

        if not await hub.async_setup_initial():
            return False

        # Store hub in runtime_data
        entry.runtime_data = hub
        # Remove old way of storing:
        # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Pass hub to async_setup_services
        await async_setup_services(hass, hub)

        entry.async_on_unload(entry.add_update_listener(async_update_options))

        async def start_websocket(_):
            await hub.async_start_websocket()

        if hass.is_running:
            await hub.async_start_websocket()
        else:
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_websocket)

        return True

    async def async_update_options(hass: HomeAssistant, entry: OpenEPaperLinkConfigEntry) -> None: # Use typed ConfigEntry
        """Handle updates to integration options."""
        # hub = hass.data[DOMAIN][entry.entry_id] # Old way
        hub = entry.runtime_data # New way
        await hub.async_reload_config()

    async def async_unload_entry(hass: HomeAssistant, entry: OpenEPaperLinkConfigEntry) -> bool: # Use typed ConfigEntry
        """Unload the integration when removed or restarted."""
        # hub = hass.data[DOMAIN][entry.entry_id] # Old way
        hub = entry.runtime_data # New way

        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        if unload_ok:
            await hub.shutdown()
            await async_unload_services(hass) # async_unload_services doesn't use the hub directly
            # hass.data[DOMAIN].pop(entry.entry_id) # No longer needed, runtime_data is managed by entry
            # if not hass.data[DOMAIN]: # Optional: clean up hass.data[DOMAIN] if empty
            #     hass.data.pop(DOMAIN)

        return unload_ok
    # ...
    ```

2.  **Modify Platform Setup Files (e.g., `sensor.py`, `switch.py`, `camera.py`, `button.py`, `text.py`, `select.py`):**
    *   In each platform's `async_setup_entry` function:
        *   Import `OpenEPaperLinkConfigEntry` (e.g., `from .. import OpenEPaperLinkConfigEntry` or `from ..__init__ import OpenEPaperLinkConfigEntry`).
        *   Import `Hub` (e.g., `from ..hub import Hub`).
        *   Change the type hint for `entry` to `OpenEPaperLinkConfigEntry`.
        *   Retrieve the `hub` instance using `hub: Hub = entry.runtime_data`.
        *   Remove the old way: `hub = hass.data[DOMAIN][entry.entry_id]`.

    Example for `sensor.py`:
    ```python
    # homeassistant/components/open_epaper_link/sensor.py
    # ...
    from homeassistant.config_entries import ConfigEntry # Keep for general type if needed elsewhere
    from homeassistant.core import HomeAssistant, callback
    # ...
    from .const import DOMAIN
    from .. import OpenEPaperLinkConfigEntry # Import the typed ConfigEntry
    from ..hub import Hub # Import Hub

    # ...
    async def async_setup_entry(
        hass: HomeAssistant,
        entry: OpenEPaperLinkConfigEntry, # Use typed ConfigEntry
        async_add_entities: AddEntitiesCallback
    ) -> None:
        """Set up the OpenEPaperLink sensors."""
        # hub = hass.data[DOMAIN][entry.entry_id] # Old way
        hub: Hub = entry.runtime_data # New way

        # Set up AP sensors
        ap_sensors = [OpenEPaperLinkAPSensor(hub, description) for description in AP_SENSOR_TYPES]
        async_add_entities(ap_sensors)
        # ... rest of the function
    ```
    Apply similar changes to all other platform setup files.

3.  **Modify `services.py`:**
    *   Update `async_setup_services` to accept the `hub` instance as a parameter.
    *   Remove the `get_hub` helper function.
    *   Service handlers (nested functions) will now have `hub` in their closure.

    ```python
    # homeassistant/components/open_epaper_link/services.py
    from __future__ import annotations
    # ...
    from homeassistant.core import HomeAssistant, ServiceCall
    # ...
    from .const import DOMAIN
    from .hub import Hub # Import Hub
    # ...

    async def async_setup_services(hass: HomeAssistant, hub: Hub) -> None: # Add hub parameter
        """Set up the OpenEPaperLink services."""

        upload_queue = UploadQueueHandler(max_concurrent=1, cooldown=1.0)

        # Remove old get_hub function:
        # async def get_hub():
        #     """Get the hub instance from Home Assistant data."""
        #     # ...
        #     return next(iter(hass.data[DOMAIN].values()))

        async def drawcustom_service(service: ServiceCall) -> None:
            """Handle drawcustom service calls."""
            # hub = await get_hub() # Old way
            # Use hub directly from the outer scope
            if not hub.online:
                raise HomeAssistantError(
                    "AP is offline. Please check your network connection and AP status."
                )
            # ... rest of the function using hub directly
        # ... similar changes for other service handlers using get_hub()
    ```

4.  **Modify `util.py`:**
    *   Update utility functions like `send_tag_cmd` and `reboot_ap` to accept the `hub` instance directly instead of `hass`.
    *   If `hass` is needed within these functions (e.g., for `async_add_executor_job`), it can be accessed via `hub.hass`.

    ```python
    # homeassistant/components/open_epaper_link/util.py
    from __future__ import annotations

    from .const import DOMAIN
    from .hub import Hub # Import Hub
    import requests
    import logging
    # from homeassistant.core import HomeAssistant # No longer needed directly for these functions
    from homeassistant.helpers.dispatcher import async_dispatcher_send
    _LOGGER = logging.getLogger(__name__)
    # ...

    async def send_tag_cmd(hub: Hub, entity_id: str, cmd: str) -> bool: # Take hub, not hass
        """Send a command to an ESL Tag."""
        # hub is passed directly

        if not hub.online:
            _LOGGER.error("Cannot send command: AP is offline")
            return False

        mac = entity_id.split(".")[1].upper()
        url = f"http://{hub.host}/tag_cmd"

        data = {
            'mac': mac,
            'cmd': cmd
        }

        try:
            # Use hub.hass for async_add_executor_job
            result = await hub.hass.async_add_executor_job(lambda: requests.post(url, data=data))
            if result.status_code == 200:
                _LOGGER.info("Sent %s command to %s", cmd, entity_id)
                return True
            else:
                _LOGGER.error("Failed to send %s command to %s: HTTP %s", cmd, entity_id, result.status_code)
                return False
        except Exception as e:
            _LOGGER.error("Failed to send %s command to %s: %s", cmd, entity_id, str(e))
            return False

    async def reboot_ap(hub: Hub) -> bool: # Take hub, not hass
        """Reboot the ESL Access Point."""
        # hub is passed directly

        if not hub.online:
            _LOGGER.error("Cannot reboot AP: AP is offline")
            return False

        url = f"http://{hub.host}/reboot"

        try:
            # Use hub.hass for async_add_executor_job
            result = await hub.hass.async_add_executor_job(lambda: requests.post(url))
            if result.status_code == 200:
                _LOGGER.info("Rebooted OEPL Access Point")
                return True
            else:
                _LOGGER.error("Failed to reboot OEPL Access Point: HTTP %s", result.status_code)
                return False
        except Exception as e:
            _LOGGER.error("Failed to reboot OEPL Access Point: %s", str(e))
            return False

    # set_ap_config_item already takes hub, so it's fine.
    # async def set_ap_config_item(hub: Hub, key: str, value: str | int) -> bool:
    ```
    Callers of these utility functions (e.g., in `button.py`) will need to be updated to pass `self._hub` (which they would have from their initialization) instead of `self.hass`.

    Example for `button.py` (`ClearPendingTagButton`):
    ```python
    # homeassistant/components/open_epaper_link/button.py
    # ...
    class ClearPendingTagButton(ButtonEntity):
        # ...
        async def async_press(self) -> None:
            """Handle the button press."""
            # await send_tag_cmd(self.hass, self._entity_id, "clear") # Old way
            await send_tag_cmd(self._hub, self._entity_id, "clear") # New way, assuming self._hub is initialized
    ```

By implementing these changes, the `open_epaper_link` integration will align with current Home Assistant best practices for managing runtime data, leading to cleaner code, improved type safety, and better maintainability.

_Created at 2025-05-14 20:39:17. Prompt tokens: 60448, Output tokens: 3149, Total tokens: 68618_
