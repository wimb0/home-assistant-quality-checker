# overkiz: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default)                                                     |
| Status | **todo**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `entity-disabled-by-default` rule applies to the `overkiz` integration as it creates numerous entities across various platforms. This rule encourages disabling less popular or noisy entities by default to conserve system resources, allowing users to enable them if needed.

The `overkiz` integration partially adheres to this rule.
It demonstrates good practice in `sensor.py`, where several `OverkizSensorDescription` instances (e.g., for `OverkizState.CORE_RSSI_LEVEL`, `OverkizState.CORE_V40_WATER_VOLUME_ESTIMATION`, various consumption tariffs, `IO_PRIORITY_LOCK_ORIGINATOR`, `CORE_PRIORITY_LOCK_TIMER`, `CORE_DISCRETE_RSSI_LEVEL`, `CORE_SENSOR_DEFECT`, and `CORE_TARGET_CLOSURE`) correctly set `entity_registry_enabled_default=False`. This is also seen in `alarm_control_panel.py`, where the `TSKALARM_CONTROLLER` is disabled by default with a clear justification in the code comments: "Disabled by default since all Overkiz hubs have this virtual device, but only a few users actually use this."
Additionally, two diagnostic buttons in `button.py` (`OverkizCommand.IDENTIFY` and `OverkizCommand.STOP_IDENTIFY`) are also correctly disabled by default.

However, there are several areas where the integration does not fully follow the rule:

1.  **Diagnostic Entities Enabled by Default:**
    *   In `sensor.py`, the `OverkizHomeKitSetupCodeSensor` (which is `EntityCategory.DIAGNOSTIC`) is enabled by default. Setup codes are typically needed only once.
    *   Several `OverkizSensorDescription` instances for diagnostic entities are enabled by default:
        *   `IO_SENSOR_ROOM` (`EntityCategory.DIAGNOSTIC`, options: "clean", "dirty").
        *   `IO_HEAT_PUMP_OPERATING_TIME` (`EntityCategory.DIAGNOSTIC`, type: duration).
        *   `IO_ELECTRIC_BOOSTER_OPERATING_TIME` (`EntityCategory.DIAGNOSTIC`, type: duration).
    *   In `button.py`, some diagnostic buttons are enabled by default:
        *   The `OverkizButtonDescription` for `OverkizCommand.START_IDENTIFY` (the one with `device_class=ButtonDeviceClass.IDENTIFY` and `EntityCategory.DIAGNOSTIC`).
        *   The `OverkizButtonDescription` for `OverkizCommand.CHECK_EVENT_TRIGGER` (SmokeSensor Test, `EntityCategory.DIAGNOSTIC`).

2.  **"Less Popular" Variant Entities:**
    *   In `cover/vertical_cover.py`, the `LowSpeedCover` entity is created in addition to the main `VerticalCover` if the device supports low-speed commands. This "Low speed" control is an additional feature that might be less popular than the primary cover operations and could be disabled by default. It currently does not set `_attr_entity_registry_enabled_default = False`.

3.  **Configuration Entities Enabled by Default:**
    *   In `number.py`, all created number entities are `EntityCategory.CONFIG` and enabled by default. While many are primary configurations, some could be considered "less popular":
        *   `OverkizState.CORE_EXPECTED_NUMBER_OF_SHOWER`.
        *   `OverkizState.CORE_BOOST_MODE_DURATION`.
        *   `OverkizState.IO_AWAY_MODE_DURATION`.
    *   In `select.py`, the select entity for `OverkizState.IO_MEMORIZED_SIMPLE_VOLUME` is `EntityCategory.CONFIG` and enabled by default. Depending on its ubiquity, it might be less popular.
    *   In `switch.py`, the switch for `UIWidget.MY_FOX_SECURITY_CAMERA` (named "Camera shutter") is `EntityCategory.CONFIG` and enabled by default. This might be a less frequently used setting.

The entity description classes for `Button`, `Number`, `Select`, and `Switch` entities inherit the `entity_registry_enabled_default` field from their respective base Home Assistant entity description classes. The task is to utilize this field by setting it to `False` for the specific descriptions identified above.

## Suggestions

To fully comply with the `entity-disabled-by-default` rule, consider the following changes:

1.  **For `sensor.py` (`homeassistant/components/overkiz/sensor.py`):**
    *   In the `OverkizHomeKitSetupCodeSensor` class, add:
        ```python
        _attr_entity_registry_enabled_default = False
        ```
    *   For the following `OverkizSensorDescription` instances in the `SENSOR_DESCRIPTIONS` list, add `entity_registry_enabled_default=False,`:
        *   The description for `key=OverkizState.IO_SENSOR_ROOM`.
        *   The description for `key=OverkizState.IO_HEAT_PUMP_OPERATING_TIME`.
        *   The description for `key=OverkizState.IO_ELECTRIC_BOOSTER_OPERATING_TIME`.

        Example for `IO_SENSOR_ROOM`:
        ```python
        OverkizSensorDescription(
            key=OverkizState.IO_SENSOR_ROOM,
            name="Sensor room",
            device_class=SensorDeviceClass.ENUM,
            options=["clean", "dirty"],
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:spray-bottle",
            translation_key="sensor_room",
            entity_registry_enabled_default=False, # Add this line
        ),
        ```

2.  **For `button.py` (`homeassistant/components/overkiz/button.py`):**
    *   For the following `OverkizButtonDescription` instances in the `BUTTON_DESCRIPTIONS` list, add `entity_registry_enabled_default=False,`:
        *   The description for `key=OverkizCommand.START_IDENTIFY` (where `device_class=ButtonDeviceClass.IDENTIFY`).
        *   The description for `key=OverkizCommand.CHECK_EVENT_TRIGGER`.

        Example for `START_IDENTIFY`:
        ```python
        OverkizButtonDescription(
            key=OverkizCommand.START_IDENTIFY,
            name="Identify",
            icon="mdi:human-greeting-variant",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=ButtonDeviceClass.IDENTIFY,
            entity_registry_enabled_default=False, # Add this line
        ),
        ```

3.  **For `cover/vertical_cover.py` (`homeassistant/components/overkiz/cover/vertical_cover.py`):**
    *   In the `LowSpeedCover` class definition, add:
        ```python
        _attr_entity_registry_enabled_default = False
        ```

4.  **For `number.py` (`homeassistant/components/overkiz/number.py`):**
    *   For the following `OverkizNumberDescription` instances in the `NUMBER_DESCRIPTIONS` list, add `entity_registry_enabled_default=False,`:
        *   The description for `key=OverkizState.CORE_EXPECTED_NUMBER_OF_SHOWER`.
        *   The description for `key=OverkizState.CORE_BOOST_MODE_DURATION`.
        *   The description for `key=OverkizState.IO_AWAY_MODE_DURATION`.

        Example for `CORE_EXPECTED_NUMBER_OF_SHOWER`:
        ```python
        OverkizNumberDescription(
            key=OverkizState.CORE_EXPECTED_NUMBER_OF_SHOWER,
            name="Expected number of shower",
            icon="mdi:shower-head",
            command=OverkizCommand.SET_EXPECTED_NUMBER_OF_SHOWER,
            native_min_value=2,
            native_max_value=4,
            min_value_state_name=OverkizState.CORE_MINIMAL_SHOWER_MANUAL_MODE,
            max_value_state_name=OverkizState.CORE_MAXIMAL_SHOWER_MANUAL_MODE,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False, # Add this line
        ),
        ```

5.  **For `select.py` (`homeassistant/components/overkiz/select.py`):**
    *   For the `OverkizSelectDescription` instance for `key=OverkizState.IO_MEMORIZED_SIMPLE_VOLUME` in the `SELECT_DESCRIPTIONS` list, add `entity_registry_enabled_default=False,`.

        Example:
        ```python
        OverkizSelectDescription(
            key=OverkizState.IO_MEMORIZED_SIMPLE_VOLUME,
            name="Memorized simple volume",
            options=[OverkizCommandParam.STANDARD, OverkizCommandParam.HIGHEST],
            select_option=_select_option_memorized_simple_volume,
            entity_category=EntityCategory.CONFIG,
            translation_key="memorized_simple_volume",
            entity_registry_enabled_default=False, # Add this line
        ),
        ```

6.  **For `switch.py` (`homeassistant/components/overkiz/switch.py`):**
    *   For the `OverkizSwitchDescription` instance for `key=UIWidget.MY_FOX_SECURITY_CAMERA` in the `SWITCH_DESCRIPTIONS` list, add `entity_registry_enabled_default=False,`.

        Example:
        ```python
        OverkizSwitchDescription(
            key=UIWidget.MY_FOX_SECURITY_CAMERA,
            name="Camera shutter",
            turn_on=OverkizCommand.OPEN,
            turn_off=OverkizCommand.CLOSE,
            icon="mdi:camera-lock",
            is_on=lambda select_state: (
                select_state(OverkizState.MYFOX_SHUTTER_STATUS)
                == OverkizCommandParam.OPENED
            ),
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False, # Add this line
        ),
        ```

By implementing these changes, entities that are diagnostic, less popular, or provide alternative/additional controls will be disabled by default, improving the user experience for most users by reducing clutter and resource usage, while still allowing advanced users to enable them as needed. This will bring the `overkiz` integration into fuller compliance with the `entity-disabled-by-default` rule.

_Created at 2025-05-28 12:37:03. Prompt tokens: 87047, Output tokens: 2585, Total tokens: 96834_
