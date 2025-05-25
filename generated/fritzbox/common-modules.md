```markdown
# fritzbox: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule requires integrations to place common patterns, specifically the data update coordinator and a base entity, into dedicated `coordinator.py` and `entity.py` files, respectively. This rule applies to the `fritzbox` integration.

Based on the provided code, the `fritzbox` integration successfully follows this rule:

1.  **Coordinator:** The integration utilizes a data update coordinator implemented in `homeassistant/components/fritzbox/coordinator.py`. The class `FritzboxDataUpdateCoordinator` inherits from `DataUpdateCoordinator`, centralizing the data fetching logic for the integration's devices and templates, as required by the rule.
2.  **Base Entity:** A base entity class is defined in `homeassistant/components/fritzbox/entity.py`. The file contains `FritzBoxEntity`, an abstract base class, and `FritzBoxDeviceEntity`, which inherits from `FritzBoxEntity` and `CoordinatorEntity`. Entities implemented in the platform files (e.g., `binary_sensor.py`, `cover.py`, `light.py`, `sensor.py`, `switch.py`, `button.py`) inherit from these base classes (specifically `FritzBoxDeviceEntity` or `FritzBoxEntity`), reducing code duplication and promoting consistency.

The structure and implementation align directly with the examples and reasoning provided in the rule documentation.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:19:48. Prompt tokens: 18905, Output tokens: 425, Total tokens: 19829_
