```markdown
# pegel_online: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule requires integrations to store runtime-specific data, such as API clients or data update coordinators, in the `ConfigEntry.runtime_data` attribute and to type the `ConfigEntry` appropriately.

This rule applies to the `pegel_online` integration because it needs to manage a `DataUpdateCoordinator` instance throughout the lifecycle of the configuration entry.

Upon reviewing the code:

1.  In `homeassistant/components/pegel_online/coordinator.py`, a custom type `PegelOnlineConfigEntry` is defined as `type PegelOnlineConfigEntry = ConfigEntry[PegelOnlineDataUpdateCoordinator]`. This correctly types the `ConfigEntry` to indicate that its `runtime_data` attribute is expected to hold a `PegelOnlineDataUpdateCoordinator`.
2.  In `homeassistant/components/pegel_online/__init__.py`, the `async_setup_entry` function is typed using `entry: PegelOnlineConfigEntry`.
3.  Inside `async_setup_entry`, a `PegelOnlineDataUpdateCoordinator` instance named `coordinator` is created.
4.  Crucially, this `coordinator` instance is then assigned to `entry.runtime_data` via the line `entry.runtime_data = coordinator`.
5.  Other parts of the integration, such as the `sensor.py` (`async_setup_entry`) and `diagnostics.py` (`async_get_config_entry_diagnostics`), correctly retrieve the coordinator instance using `coordinator = entry.runtime_data`.

The integration correctly implements the requirement to store the coordinator in `ConfigEntry.runtime_data` and uses the recommended typing pattern. Therefore, the integration fully complies with this rule.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:22:32. Prompt tokens: 5855, Output tokens: 501, Total tokens: 7100_
