# fritzbox: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data) |
| Status | **done**                                                                 |

## Overview

The `runtime-data` rule requires integrations using configuration entries to store non-persistent runtime data in the `ConfigEntry.runtime_data` attribute, using a custom typed `ConfigEntry` alias if strict typing is enforced.

This rule applies to the `fritzbox` integration as it uses `ConfigEntry` to manage connections and fetch data from the FRITZ!Box, which constitutes runtime data.

The `fritzbox` integration fully follows this rule.
- It defines a custom type alias `FritzboxConfigEntry = ConfigEntry[FritzboxDataUpdateCoordinator]` in `homeassistant/components/fritzbox/coordinator.py`, ensuring type safety for the data stored in `runtime_data`. This is necessary because the integration uses strict typing.
- In the `async_setup_entry` function within `homeassistant/components/fritzbox/__init__.py`, it correctly initializes the `FritzboxDataUpdateCoordinator` instance:
  ```python
  coordinator = FritzboxDataUpdateCoordinator(hass, entry)
  await coordinator.async_setup()
  entry.runtime_data = coordinator
  ```
  This assigns the coordinator object, which holds the `pyfritzhome` connection and fetched data, to `entry.runtime_data`.
- The `FritzboxConfigEntry` type hint is used for the `entry` parameter in `async_setup_entry`, `async_unload_entry`, and `async_remove_config_entry_device` in `__init__.py`, as well as in the platform `async_setup_entry` functions (e.g., `homeassistant/components/fritzbox/binary_sensor.py`).
- All platforms and internal functions needing access to the coordinator (like `async_unload_entry` and `async_remove_config_entry_device` in `__init__.py`, and the entity base classes) retrieve the coordinator instance from `entry.runtime_data`.

This implementation correctly leverages `ConfigEntry.runtime_data` for storing the integration's primary runtime object in a typed and consistent manner.

## Suggestions

No suggestions needed.

_Created at 2025-05-25 11:20:43. Prompt tokens: 18950, Output tokens: 562, Total tokens: 20490_
