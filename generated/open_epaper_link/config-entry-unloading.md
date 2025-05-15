# open_epaper_link: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **todo**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `config-entry-unloading` rule requires that integrations support config entry unloading by implementing the `async_unload_entry` function. This function must clean up all resources established during `async_setup_entry`, such as listeners, connections, and registered platforms.

This rule applies to the `open_epaper_link` integration because it uses config entries (as indicated by `config_flow: true` in `manifest.json` and the presence of `config_flow.py`) and sets up various resources:
*   Entity platforms (Sensor, Button, Camera, Select, Switch, Text).
*   A `Hub` instance, which manages a WebSocket connection to the OpenEPaperLink Access Point.
*   Custom services.
*   Data stored in `hass.data`.
*   Event listeners.

The `open_epaper_link` integration implements an `async_unload_entry` function in `__init__.py`. This function correctly handles several aspects of resource cleanup:

1.  **Platform Unloading:** It calls `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` to unload all registered entity platforms.
2.  **Hub Shutdown:** It calls `await hub.shutdown()`. The `Hub.shutdown()` method (in `hub.py`) appears to correctly handle the termination of its WebSocket connection by cancelling the `_ws_task` and setting a `_shutdown` event flag to prevent reconnection attempts.
3.  **Service Unloading:** It calls `await async_unload_services(hass)`. The `async_unload_services` function (in `services.py`) correctly removes all services that were registered by `async_setup_services`.
4.  **Data Cleanup:** It removes the `Hub` instance from `hass.data` using `hass.data[DOMAIN].pop(entry.entry_id)`.
5.  **Update Listener Cleanup:** In `async_setup_entry`, `entry.async_on_unload(entry.add_update_listener(async_update_options))` is used, which correctly ensures the options update listener is cleaned up when the entry is unloaded.

However, there is one subscription made in `async_setup_entry` that is not properly cleaned up:

*   In `__init__.py`, within `async_setup_entry`, if Home Assistant is not yet running (`else` block of `if hass.is_running:`), a listener for `EVENT_HOMEASSISTANT_STARTED` is registered:
    ```python
    # __init__.py
    # ...
    else:
        # Otherwise wait for the started event
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_websocket)
    ```
    This `async_listen_once` subscription is not explicitly removed in `async_unload_entry`, nor is its cleanup callback registered via `entry.async_on_unload`. If the config entry is unloaded *before* `EVENT_HOMEASSISTANT_STARTED` fires, this listener will remain active. When the event eventually fires, `start_websocket` will be called. This callback attempts to use the `hub` instance from its closure, which would have already been "shut down" and removed from `hass.data`. This could lead to errors or unexpected behavior as `hub.async_start_websocket()` might be called on a defunct object or attempt to re-establish a WebSocket connection inappropriately.

Because this specific listener is not cleaned up, the integration does not fully follow the `config-entry-unloading` rule, which mandates cleaning up *all* subscriptions.

## Suggestions

To make the `open_epaper_link` integration compliant with the `config-entry-unloading` rule, the `hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_websocket)` subscription needs to be cleaned up when the config entry is unloaded.

This can be achieved by registering the cleanup function (returned by `async_listen_once`) with `entry.async_on_unload` within the `async_setup_entry` function.

Modify the following section in `homeassistant/components/open_epaper_link/__init__.py`:

```python
    # ...
    if hass.is_running:
        # If HA is already running, start WebSocket immediately
        await hub.async_start_websocket()
    else:
        # Otherwise wait for the started event
        # OLD: hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_websocket)
        # NEW: Register the listener's cleanup with entry.async_on_unload
        entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_websocket)
        )

    return True
```

**Reasoning for the suggestion:**

By wrapping the `hass.bus.async_listen_once(...)` call with `entry.async_on_unload(...)`, Home Assistant will automatically call the unregistration function for this listener when the config entry is unloaded. This ensures that:
1.  If the entry is unloaded before `EVENT_HOMEASSISTANT_STARTED` fires, the listener is removed, and `start_websocket` will not be called.
2.  If `EVENT_HOMEASSISTANT_STARTED` has already fired, `async_listen_once` would have already executed and removed itself. Calling the unregistration function again is typically safe and a no-op.

This change ensures all subscriptions made during `async_setup_entry` are properly cleaned up, fulfilling the requirements of the `config-entry-unloading` rule.

_Created at 2025-05-14 20:45:30. Prompt tokens: 60513, Output tokens: 1375, Total tokens: 66660_
