# wled: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `config-entry-unloading` rule requires integrations to implement the `async_unload_entry` function to allow Home Assistant to unload the integration at runtime. This function must clean up all resources, such as connections and subscriptions, that were established during the setup of the config entry.

The `wled` integration correctly implements this rule.

1.  **Presence of `async_unload_entry`**:
    The integration defines the `async_unload_entry` function in its `__init__.py` file:
    ```python
    # __init__.py
    async def async_unload_entry(hass: HomeAssistant, entry: WLEDConfigEntry) -> bool:
        """Unload WLED config entry."""
        if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
            coordinator = entry.runtime_data

            # Ensure disconnected and cleanup stop sub
            await coordinator.wled.disconnect()
            if coordinator.unsub:
                coordinator.unsub()

        return unload_ok
    ```

2.  **Unloading Platforms**:
    The function first calls `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` to unload all entities associated with the config entry across the defined `PLATFORMS` (button, light, number, select, sensor, switch, update). This is the standard and required way to clean up entities.

3.  **Resource Cleanup**:
    If platform unloading is successful (`unload_ok` is true), the integration proceeds to clean up its specific resources:
    *   `coordinator = entry.runtime_data`: Retrieves the `WLEDDataUpdateCoordinator` instance.
    *   `await coordinator.wled.disconnect()`: This is a crucial step. It calls the `disconnect` method on the WLED client instance (`self.wled` in the coordinator). This method is responsible for closing any active connections to the WLED device, including WebSockets if they were in use. This prevents lingering connections and resource leaks.
    *   `if coordinator.unsub: coordinator.unsub()`: The `coordinator.unsub` attribute stores a callback to unsubscribe from an event listener (`EVENT_HOMEASSISTANT_STOP`), which is set up if the coordinator uses a WebSocket connection (`coordinator.py`, `_use_websocket` method). This line ensures that this event listener is removed, preventing it from being called after the entry is unloaded and cleaning up the subscription.

4.  **Return Value**:
    The function returns `unload_ok`, which is the boolean result from `hass.config_entries.async_unload_platforms`. This correctly signals to Home Assistant whether the unloading process was successful.

5.  **Background Task Management**:
    The `WLEDDataUpdateCoordinator` may create a background task for WebSocket listening using `entry.async_create_background_task`. Home Assistant automatically cancels tasks created this way when the associated config entry is unloaded. The explicit `coordinator.wled.disconnect()` call ensures the underlying library connection used by this task is terminated gracefully.

6.  **`entry.async_on_unload` Usage**:
    In `async_setup_entry`, `entry.async_on_unload(entry.add_update_listener(async_reload_entry))` is used. This is a standard pattern for registering a listener that reloads the config entry when its options are changed. The callback returned by `add_update_listener` is automatically cleaned up by `entry.async_on_unload` when the entry is unloaded, which is the correct behavior.

The implementation in `wled/__init__.py` effectively cleans up platforms, network connections, and event subscriptions, fully satisfying the requirements of the `config-entry-unloading` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:54:01. Prompt tokens: 21415, Output tokens: 949, Total tokens: 26204_
