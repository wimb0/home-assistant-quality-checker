# overkiz: entity-category

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [entity-category](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-category)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `entity-category` rule requires that entities are assigned an appropriate `EntityCategory` (e.g., `DIAGNOSTIC`, `CONFIG`) when the default category (`None`, implying a primary control or sensor) is inappropriate. This helps in organizing entities and is used by features like auto-generated dashboards.

The `overkiz` integration applies this rule because it creates a variety of entities, some of which serve diagnostic or configuration purposes rather than being primary controls or sensors.

The integration already correctly assigns entity categories in many instances:
*   Several `sensor` entities (e.g., battery levels, RSSI, sensor defects, HomeKit setup code) are correctly marked as `EntityCategory.DIAGNOSTIC`.
*   Many `number` entities (e.g., "My position" for covers, various temperature setpoints for water heaters and climate devices, boost/away mode durations) are correctly marked as `EntityCategory.CONFIG`.
*   Certain `button` entities (e.g., identify, smoke sensor test) are correctly marked as `EntityCategory.DIAGNOSTIC`.
*   The "Camera shutter" `switch` entity is correctly marked as `EntityCategory.CONFIG`.
*   Some `select` entities (e.g., "Memorized simple volume", "Operating mode" for heating interface) are correctly marked as `EntityCategory.CONFIG`.

However, there are several sensor and binary_sensor entities that appear to be diagnostic in nature but are not assigned an `entity_category`, meaning they default to `None`. This makes them appear as primary sensors when they are more suited to a `DIAGNOSTIC` classification.

Specifically, the following entities are missing an appropriate `EntityCategory`:

**In `sensor.py` (`SENSOR_DESCRIPTIONS`):**
*   `OverkizSensorDescription` for `key=OverkizState.IO_PRIORITY_LOCK_ORIGINATOR` (name: "Priority lock originator"): This sensor indicates the source of a priority lock, which is diagnostic information.
*   `OverkizSensorDescription` for `key=OverkizState.CORE_PRIORITY_LOCK_TIMER` (name: "Priority lock timer"): This sensor shows the remaining time for a priority lock, which is diagnostic.
*   `OverkizSensorDescription` for `key=OverkizState.CORE_TARGET_CLOSURE` (name: "Target closure"): This sensor indicates the intended position of a cover. While related to control, the target itself (especially when `entity_registry_enabled_default=False`) is often used for diagnostic purposes.
*   `OverkizSensorDescription` for `key=OverkizState.CORE_NUMBER_OF_SHOWER_REMAINING` (name: "Number of shower remaining"): This is a derived status about capacity, fitting a diagnostic role.
*   `OverkizSensorDescription` for `key=OverkizState.CORE_V40_WATER_VOLUME_ESTIMATION` (name: "Water volume estimation at 40 °C"): An "estimation" implies a derived or calculated value, suitable for diagnostics, especially with `entity_registry_enabled_default=False`.

**In `binary_sensor.py` (`BINARY_SENSOR_DESCRIPTIONS`):**
*   `OverkizBinarySensorDescription` for `key=OverkizState.IO_OPERATING_MODE_CAPABILITIES` (name: "Energy Demand Status"): This binary sensor indicates a system capability or status, which is diagnostic information.

## Suggestions

To comply with the `entity-category` rule, the following changes are recommended:

1.  **For `sensor.py`:**
    Modify the `OverkizSensorDescription` entries in the `SENSOR_DESCRIPTIONS` list:

    *   For `OverkizState.IO_PRIORITY_LOCK_ORIGINATOR`:
        ```python
        OverkizSensorDescription(
            key=OverkizState.IO_PRIORITY_LOCK_ORIGINATOR,
            name="Priority lock originator",
            icon="mdi:lock",
            entity_registry_enabled_default=False,
            translation_key="priority_lock_originator",
            native_value=lambda value: OVERKIZ_STATE_TO_TRANSLATION.get(
                cast(str, value), cast(str, value)
            ),
            entity_category=EntityCategory.DIAGNOSTIC, # Suggested addition
        ),
        ```

    *   For `OverkizState.CORE_PRIORITY_LOCK_TIMER`:
        ```python
        OverkizSensorDescription(
            key=OverkizState.CORE_PRIORITY_LOCK_TIMER,
            name="Priority lock timer",
            icon="mdi:lock-clock",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_registry_enabled_default=False,
            entity_category=EntityCategory.DIAGNOSTIC, # Suggested addition
        ),
        ```

    *   For `OverkizState.CORE_TARGET_CLOSURE`:
        ```python
        OverkizSensorDescription(
            key=OverkizState.CORE_TARGET_CLOSURE,
            name="Target closure",
            native_unit_of_measurement=PERCENTAGE,
            entity_registry_enabled_default=False,
            entity_category=EntityCategory.DIAGNOSTIC, # Suggested addition
        ),
        ```

    *   For `OverkizState.CORE_NUMBER_OF_SHOWER_REMAINING`:
        ```python
        OverkizSensorDescription(
            key=OverkizState.CORE_NUMBER_OF_SHOWER_REMAINING,
            name="Number of shower remaining",
            icon="mdi:shower-head",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC, # Suggested addition
        ),
        ```

    *   For `OverkizState.CORE_V40_WATER_VOLUME_ESTIMATION`:
        ```python
        OverkizSensorDescription(
            key=OverkizState.CORE_V40_WATER_VOLUME_ESTIMATION,
            name="Water volume estimation at 40 °C",
            icon="mdi:water",
            native_unit_of_measurement=UnitOfVolume.LITERS,
            device_class=SensorDeviceClass.VOLUME_STORAGE,
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC, # Suggested addition
        ),
        ```

2.  **For `binary_sensor.py`:**
    Modify the `OverkizBinarySensorDescription` entry in the `BINARY_SENSOR_DESCRIPTIONS` list:

    *   For `OverkizState.IO_OPERATING_MODE_CAPABILITIES`:
        ```python
        OverkizBinarySensorDescription(
            key=OverkizState.IO_OPERATING_MODE_CAPABILITIES,
            name="Energy Demand Status",
            device_class=BinarySensorDeviceClass.HEAT,
            value_fn=lambda state: cast(dict, state).get(
                OverkizCommandParam.ENERGY_DEMAND_STATUS
            )
            == 1,
            entity_category=EntityCategory.DIAGNOSTIC, # Suggested addition
        ),
        ```

**Reasoning for Suggestions:**
Adding `entity_category=EntityCategory.DIAGNOSTIC` to these sensor descriptions correctly classifies them as providing secondary, diagnostic information about the devices or system, rather than primary control data or measurements. This aligns with the intent of the `entity-category` rule and improves the user experience by better organizing entities in Home Assistant.

_Created at 2025-05-28 12:33:48. Prompt tokens: 86709, Output tokens: 1851, Total tokens: 93949_
