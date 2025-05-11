# wled: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule mandates that common patterns like data coordinators and base entities should be placed in dedicated files, `coordinator.py` and `entity.py` respectively, to enhance consistency and maintainability.

This rule applies to the `wled` integration as it utilizes both a data update coordinator pattern and a base entity pattern.

The integration fully follows this rule:

1.  **Coordinator:**
    The integration uses two data update coordinators: `WLEDDataUpdateCoordinator` for device-specific data and `WLEDReleasesDataUpdateCoordinator` for WLED firmware release information. Both of these coordinators are correctly defined in the `coordinator.py` file.
    *   `WLEDDataUpdateCoordinator` is defined in `coordinator.py` (lines 28-98).
    *   `WLEDReleasesDataUpdateCoordinator` is defined in `coordinator.py` (lines 101-118).
    These coordinators are then imported and used in `__init__.py`, `update.py`, and other entity platform files.

2.  **Base Entity:**
    The integration defines a base entity class `WLEDEntity` to share common logic and properties (like `device_info`) across its various entity platforms. This base entity is correctly defined in the `entity.py` file.
    *   `WLEDEntity` is defined in `entity.py` (lines 8-25).
    This `WLEDEntity` class is subsequently imported and inherited by entities in `button.py`, `light.py`, `number.py`, `select.py`, `sensor.py`, `switch.py`, and `update.py`.

The placement of these common components in their designated `coordinator.py` and `entity.py` files aligns with the rule's requirements, promoting code organization and consistency.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:24:52. Prompt tokens: 21007, Output tokens: 523, Total tokens: 22153_
