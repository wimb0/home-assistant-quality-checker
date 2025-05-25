# samsungtv: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

This rule requires integrations to store integration-specific runtime data, such as client connections or update coordinators, in the `ConfigEntry.runtime_data` attribute. It also recommends typing the `ConfigEntry` for better code clarity and tooling support.

The `samsungtv` integration **follows** this rule.

Upon successful setup in `__init__.py`, the integration creates a `SamsungTVDataUpdateCoordinator`. This coordinator instance is then assigned to `entry.runtime_data`:

```python
# homeassistant/components/samsungtv/__init__.py
# ...
    coordinator = SamsungTVDataUpdateCoordinator(hass, entry, bridge)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
# ...
```

The integration also defines and uses a typed `ConfigEntry` in `coordinator.py`:

```python
# homeassistant/components/samsungtv/coordinator.py
# ...
type SamsungTVConfigEntry = ConfigEntry[SamsungTVDataUpdateCoordinator]
# ...
class SamsungTVDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Coordinator for the SamsungTV integration."""

    config_entry: SamsungTVConfigEntry
# ...
```
This typed `SamsungTVConfigEntry` is correctly used in `__init__.py`, `media_player.py`, `remote.py`, and `diagnostics.py` when accessing the config entry and its `runtime_data`. For example, in `media_player.py`:

```python
# homeassistant/components/samsungtv/media_player.py
# ...
async def async_setup_entry(
    hass: HomeAssistant,
    entry: SamsungTVConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Samsung TV from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([SamsungTVDevice(coordinator)])
# ...
```
And in `diagnostics.py`:

```python
# homeassistant/components/samsungtv/diagnostics.py
# ...
async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SamsungTVConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
# ...
```

This pattern demonstrates correct usage of `runtime_data` for storing the main coordination object and accessing it in platform setup functions and diagnostics.

## Suggestions

No suggestions needed. The integration correctly uses `ConfigEntry.runtime_data` and a typed ConfigEntry.

_Created at 2025-05-25 11:28:45. Prompt tokens: 30093, Output tokens: 717, Total tokens: 31298_
