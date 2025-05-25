```markdown
# samsungtv: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that an integration implements the `async_unload_entry` function to properly clean up resources when a config entry is unloaded, allowing Home Assistant to remove or reload the integration instance without a full restart. The rule also highlights the use of `entry.async_on_unload` as a recommended way to register cleanup callbacks.

The `samsungtv` integration fully complies with this rule.

The `homeassistant/components/samsungtv/__init__.py` file contains the `async_unload_entry` function:

```python
async def async_unload_entry(hass: HomeAssistant, entry: SamsungTVConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```

This function correctly calls `hass.config_entries.async_unload_platforms`, which is the standard mechanism to unload all associated platforms (like `media_player` and `remote` defined in `PLATFORMS`). Unloading the platforms triggers the `async_will_remove_from_hass` method on the entities, which is used for entity-specific cleanup.

Furthermore, the `async_setup_entry` function in the same file registers several cleanup callbacks using `entry.async_on_unload`:

*   It registers a callback (`stop_bridge`) that calls `await bridge.async_close_remote()` when the entry is unloaded. This ensures the connection to the TV is properly closed (`homeassistant/components/samsungtv/bridge.py` defines `async_close_remote` for all bridge types).
*   It registers `debounced_reloader.async_shutdown` and cleans up the update listener associated with the entry, ensuring no background tasks related to reloading or debouncing remain active.

The `SamsungTVDevice` entity (`homeassistant/components/samsungtv/media_player.py`) also implements `async_will_remove_from_hass`, which is called when the media player platform is unloaded by `async_unload_platforms`. This method handles the specific cleanup related to the UPnP/DMR device and its associated notify server and subscriptions: `await self._async_shutdown_dmr()`.

By combining the standard platform unloading (`async_unload_platforms`) with resource-specific cleanup registered via `entry.async_on_unload` and within the entity's lifecycle (`async_will_remove_from_hass`), the integration ensures all necessary resources are released when the config entry is unloaded, fulfilling the rule's requirements.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:29:47. Prompt tokens: 30158, Output tokens: 683, Total tokens: 31943_
