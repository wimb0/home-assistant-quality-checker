```markdown
# pegel_online: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires integrations using config entries to implement the `async_unload_entry` function to support runtime unloading and clean up resources.

The `pegel_online` integration uses config entries, as indicated by `"config_flow": true` in its `manifest.json` and the presence of `async_setup_entry` in `__init__.py`. Therefore, this rule applies.

The integration fully follows this rule. It implements the `async_unload_entry` function in `homeassistant/components/pegel_online/__init__.py`. This function correctly calls `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)`, which is the standard mechanism for unloading entities associated with the config entry.

The integration utilizes a `DataUpdateCoordinator` (`PegelOnlineDataUpdateCoordinator`). The lifecycle of the `DataUpdateCoordinator`, including the stopping of its update interval, is typically managed by Home Assistant when the associated config entry and its platforms are unloaded. The API client (`aiopegelonline.PegelOnline`) uses Home Assistant's shared aiohttp client session, which doesn't require explicit closing by the integration during unload. Storing the coordinator in `entry.runtime_data` is standard practice, and explicit cleanup of the coordinator object itself within `async_unload_entry` is not necessary when using `DataUpdateCoordinator` as its lifecycle is tied to the entry.

The implementation provided satisfies the requirements of the rule by allowing the config entry and its components (entities managed by the coordinator) to be unloaded cleanly.

```python
async def async_unload_entry(
    hass: HomeAssistant, entry: PegelOnlineConfigEntry
) -> bool:
    """Unload PEGELONLINE entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```

This code snippet from `__init__.py` demonstrates the correct implementation of `async_unload_entry`.

## Suggestions

No suggestions needed.

```
```

_Created at 2025-05-25 11:23:23. Prompt tokens: 5920, Output tokens: 556, Total tokens: 7540_
