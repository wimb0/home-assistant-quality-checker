# overkiz: entity-device-class

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [entity-device-class](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-device-class)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `entity-device-class` rule requires integrations to assign a `device_class` to entities where appropriate. Device classes provide context to entities, enabling features like unit conversion, specific UI representations, and improved voice assistant integration.

The `overkiz` integration creates several entity types that support device classes, including sensors, binary sensors, covers, switches, numbers, and buttons. The rule is therefore applicable.

The integration generally makes good use of device classes, especially for:
*   **Sensors**: Many `OverkizSensorDescription` entries in `sensor.py` correctly assign `SensorDeviceClass` (e.g., `BATTERY`, `TEMPERATURE`, `HUMIDITY`, `POWER`, `ENERGY`, `ILLUMINANCE`, `VOLUME_STORAGE`, `WATER`, `GAS`, `CO`, `CO2`, `SIGNAL_STRENGTH`, `WIND_SPEED`, `DURATION`, `VOLUME_FLOW_RATE`, `ENUM`).
*   **Covers**: `VerticalCover` and `Awning` entities in `cover/vertical_cover.py` and `cover/awning.py` correctly use `CoverDeviceClass` by mapping `UIClass` or `UIWidget` or setting it directly (e.g., `CoverDeviceClass.BLIND`, `CoverDeviceClass.SHUTTER`, `CoverDeviceClass.AWNING`).
*   **Binary Sensors**: Many `OverkizBinarySensorDescription` entries in `binary_sensor.py` correctly assign `BinarySensorDeviceClass` (e.g., `SMOKE`, `MOISTURE`, `GAS`, `OCCUPANCY`, `VIBRATION`, `DOOR`, `PROBLEM`, `HEAT`).
*   **Switches**: The `OnOff` UIClass is correctly assigned `SwitchDeviceClass.OUTLET` in `switch.py`. Other switches correctly default to `SwitchDeviceClass.SWITCH`.
*   **Numbers**: Several `OverkizNumberDescription` entries in `number.py` correctly assign `NumberDeviceClass` (e.g., `TEMPERATURE`, `DURATION`).
*   **Buttons**: One of the "Identify" buttons correctly uses `ButtonDeviceClass.IDENTIFY` in `button.py`.

However, there are a few instances where device classes are applicable but are currently missing or could be added:

**Sensor Entities (`sensor.py`):**
1.  The sensor for `OverkizState.IO_INLET_ENGINE` (name: "Inlet engine") has `native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR` but is missing `device_class=SensorDeviceClass.VOLUME_FLOW_RATE`.
2.  The sensor for `OverkizState.IO_PRIORITY_LOCK_ORIGINATOR` (name: "Priority lock originator") represents a textual state from a set of options and is missing `device_class=SensorDeviceClass.ENUM`. The `options` attribute would also need to be defined for the entity description.
3.  The sensor for `OverkizState.CORE_PRIORITY_LOCK_TIMER` (name: "Priority lock timer") has `native_unit_of_measurement=UnitOfTime.SECONDS` and is missing `device_class=SensorDeviceClass.DURATION`.

**Binary Sensor Entities (`binary_sensor.py`):**
1.  The binary sensor for `OverkizState.MODBUSLINK_DHW_BOOST_MODE` (name: "Boost mode") indicates if a boost mode is active. This could potentially use `device_class=BinarySensorDeviceClass.RUNNING` to signify an active, high-performance state.

**Button Entities (`button.py`):**
1.  The `OverkizButtonDescription` with `key=OverkizCommand.IDENTIFY` and `name="Start identify"` is missing `device_class=ButtonDeviceClass.IDENTIFY`. Another button description with `key=OverkizCommand.START_IDENTIFY` and `name="Identify"` *does* correctly set this device class. If the former is a distinct, used button, it should also have the device class.

For entities like `AlarmControlPanelEntity`, `LightEntity`, `LockEntity`, `ClimateEntity`, `SirenEntity`, `WaterHeaterEntity`, and `SelectEntity`, Home Assistant core does not typically define a `_attr_device_class` in the same way as sensors or binary sensors. Their context is usually established through other properties (e.g., color modes for lights, HVAC modes for climate). Thus, the absence of `_attr_device_class` for these is acceptable.

## Suggestions

To make the `overkiz` integration fully compliant with the `entity-device-class` rule, the following changes are recommended:

1.  **In `homeassistant/components/overkiz/sensor.py`:**
    *   For the `OverkizSensorDescription` corresponding to `OverkizState.IO_INLET_ENGINE`:
        ```python
        # Before
        OverkizSensorDescription(
            key=OverkizState.IO_INLET_ENGINE,
            name="Inlet engine",
            icon="mdi:fan-chevron-up",
            native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        # After
        OverkizSensorDescription(
            key=OverkizState.IO_INLET_ENGINE,
            name="Inlet engine",
            icon="mdi:fan-chevron-up",
            native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
            device_class=SensorDeviceClass.VOLUME_FLOW_RATE, # Added
            state_class=SensorStateClass.MEASUREMENT,
        ),
        ```
        **Reason:** The sensor measures volume flow rate, and `SensorDeviceClass.VOLUME_FLOW_RATE` directly corresponds to this.

    *   For the `OverkizSensorDescription` corresponding to `OverkizState.IO_PRIORITY_LOCK_ORIGINATOR`:
        ```python
        # Before
        OverkizSensorDescription(
            key=OverkizState.IO_PRIORITY_LOCK_ORIGINATOR,
            name="Priority lock originator",
            icon="mdi:lock",
            entity_registry_enabled_default=False,
            translation_key="priority_lock_originator",
            native_value=lambda value: OVERKIZ_STATE_TO_TRANSLATION.get(
                cast(str, value), cast(str, value)
            ),
        ),
        # After
        OverkizSensorDescription(
            key=OverkizState.IO_PRIORITY_LOCK_ORIGINATOR,
            name="Priority lock originator",
            icon="mdi:lock",
            entity_registry_enabled_default=False,
            translation_key="priority_lock_originator",
            device_class=SensorDeviceClass.ENUM, # Added
            options=[*OVERKIZ_STATE_TO_TRANSLATION.keys()], # Added (or a relevant subset)
            native_value=lambda value: OVERKIZ_STATE_TO_TRANSLATION.get(
                cast(str, value), cast(str, value)
            ),
        ),
        ```
        **Reason:** This sensor reports a textual state from a known set of values. `SensorDeviceClass.ENUM` is appropriate. The `options` attribute should list the possible string values this sensor can take.

    *   For the `OverkizSensorDescription` corresponding to `OverkizState.CORE_PRIORITY_LOCK_TIMER`:
        ```python
        # Before
        OverkizSensorDescription(
            key=OverkizState.CORE_PRIORITY_LOCK_TIMER,
            name="Priority lock timer",
            icon="mdi:lock-clock",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_registry_enabled_default=False,
        ),
        # After
        OverkizSensorDescription(
            key=OverkizState.CORE_PRIORITY_LOCK_TIMER,
            name="Priority lock timer",
            icon="mdi:lock-clock",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            device_class=SensorDeviceClass.DURATION, # Added
            entity_registry_enabled_default=False,
        ),
        ```
        **Reason:** The sensor measures a time duration in seconds, making `SensorDeviceClass.DURATION` the correct class.

2.  **In `homeassistant/components/overkiz/binary_sensor.py`:**
    *   For the `OverkizBinarySensorDescription` corresponding to `OverkizState.MODBUSLINK_DHW_BOOST_MODE`:
        ```python
        # Before
        OverkizBinarySensorDescription(
            key=OverkizState.MODBUSLINK_DHW_BOOST_MODE,
            name="Boost mode",
            value_fn=(
                lambda state: state in (OverkizCommandParam.ON, OverkizCommandParam.PROG)
            ),
        ),
        # After
        OverkizBinarySensorDescription(
            key=OverkizState.MODBUSLINK_DHW_BOOST_MODE,
            name="Boost mode",
            device_class=BinarySensorDeviceClass.RUNNING, # Added
            value_fn=(
                lambda state: state in (OverkizCommandParam.ON, OverkizCommandParam.PROG)
            ),
        ),
        ```
        **Reason:** "Boost mode" implies the device is actively running in a special, typically higher-effort, state. `BinarySensorDeviceClass.RUNNING` can represent this.

3.  **In `homeassistant/components/overkiz/button.py`:**
    *   For the `OverkizButtonDescription` with `key=OverkizCommand.IDENTIFY` and `name="Start identify"`:
        ```python
        # Before
        OverkizButtonDescription(
            key=OverkizCommand.IDENTIFY,
            name="Start identify",
            icon="mdi:human-greeting-variant",
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        ),
        # After
        OverkizButtonDescription(
            key=OverkizCommand.IDENTIFY,
            name="Start identify",
            icon="mdi:human-greeting-variant",
            device_class=ButtonDeviceClass.IDENTIFY, # Added
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        ),
        ```
        **Reason:** This button initiates an identification action, making `ButtonDeviceClass.IDENTIFY` the appropriate class. This assumes this description is distinct from the other "Identify" button that already has this class. If it's redundant or a typo, it should be addressed accordingly.

By implementing these suggestions, the `overkiz` integration will better adhere to the `entity-device-class` rule, improving the user experience and consistency within Home Assistant.

_Created at 2025-05-28 12:35:29. Prompt tokens: 86982, Output tokens: 2618, Total tokens: 97499_
