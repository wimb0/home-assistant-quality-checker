```markdown
# fritzbox: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that all Python code within the integration uses type hints extensively. It also notes that if the integration uses `runtime-data`, a custom typed `ConfigEntry` is required and must be used throughout. The `fritzbox` integration uses `runtime_data` in its `__init__.py` file (`entry.runtime_data = coordinator`).

Based on the provided code, the `fritzbox` integration fully adheres to the `strict-typing` rule:

1.  **Extensive Type Hinting:** All provided Python files (`__init__.py`, `coordinator.py`, `entity.py`, `model.py`, `binary_sensor.py`, `cover.py`, `switch.py`, `const.py`, `sensor.py`, `light.py`, `button.py`, `climate.py`, `diagnostics.py`) consistently use type hints for function arguments, return values, variable assignments, and class attributes.
2.  **`__future__.annotations`:** The `from __future__ import annotations` import is present in relevant files, enabling modern type hinting syntax.
3.  **Typed ConfigEntry:** The integration correctly defines a custom typed `ConfigEntry` alias (`type FritzboxConfigEntry = ConfigEntry[FritzboxDataUpdateCoordinator]`) in `coordinator.py` and uses this alias as the type hint for the `entry` parameter in functions and methods that interact with the config entry (`async_setup_entry`, `async_unload_entry` in `__init__.py`, `__init__` in `coordinator.py`, etc.). This satisfies the requirement when using `runtime-data`.
4.  **Typed Coordinator and Data:** The `FritzboxDataUpdateCoordinator` is correctly typed using `DataUpdateCoordinator[FritzboxCoordinatorData]`, and the `FritzboxCoordinatorData` itself is a typed `@dataclass`.
5.  **Typed Entities:** The base entity `FritzBoxEntity` and its subclasses inherit from `CoordinatorEntity` and are correctly typed with the custom coordinator type (`CoordinatorEntity[FritzboxDataUpdateCoordinator]`).
6.  **Typed Descriptions and Models:** The `model.py` file and entity description classes (e.g., `FritzBinarySensorEntityDescription`, `FritzSensorEntityDescription`) use `TypedDict` and `@dataclass` with explicit type hints for their fields and callables.

The code demonstrates a comprehensive implementation of type hints throughout the integration, including the specific requirements related to using `runtime-data`. This indicates that the integration is designed for strict type checking.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:38:37. Prompt tokens: 18864, Output tokens: 679, Total tokens: 21075_
