# samsungtv: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **done**                                                                 |

## Overview

This rule requires that the integration makes extensive use of type hints to allow for static type checking. It also requires that if `runtime_data` is used with a `ConfigEntry`, a custom typed `ConfigEntry` (e.g., `ConfigEntry[MyCoordinator]`) is defined and used where appropriate.

The `samsungtv` integration fully follows the `strict-typing` rule.

The codebase demonstrates widespread use of type hints across all Python files (`__init__.py`, `bridge.py`, `config_flow.py`, `coordinator.py`, `device_trigger.py`, `diagnostics.py`, `entity.py`, `helpers.py`, `media_player.py`, `remote.py`, `trigger.py`, `triggers/turn_on.py`). Functions, methods, variables, and return types are consistently annotated.

Furthermore, the integration utilizes `runtime_data` in `homeassistant/components/samsungtv/__init__.py` where the `SamsungTVDataUpdateCoordinator` is assigned to `entry.runtime_data`. To comply with the rule's specific requirement for `runtime_data`, the integration correctly defines a custom typed `ConfigEntry` in `homeassistant/components/samsungtv/coordinator.py`:

```python
# homeassistant/components/samsungtv/coordinator.py
type SamsungTVConfigEntry = ConfigEntry[SamsungTVDataUpdateCoordinator]
```

This custom type `SamsungTVConfigEntry` is then appropriately used in function signatures and variable annotations throughout the relevant parts of the integration, such as in `async_setup_entry`, `_async_update_ssdp_locations`, `async_migrate_entry`, and within the `CoordinatorEntity` base class definition in `homeassistant/components/samsungtv/entity.py`, ensuring that access to `config_entry.runtime_data` is correctly typed as `SamsungTVDataUpdateCoordinator`.

The comprehensive type hinting and the correct implementation of the custom typed `ConfigEntry` for `runtime_data` usage indicate that the integration is designed to be statically type checked, fulfilling the requirements of the `strict-typing` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-25 11:33:48. Prompt tokens: 30007, Output tokens: 571, Total tokens: 32105_
