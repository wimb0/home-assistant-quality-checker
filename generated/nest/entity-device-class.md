# nest: entity-device-class

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [entity-device-class](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-device-class)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `entity-device-class` rule requires that entities use device classes where possible to provide context, which Home Assistant uses for UI representation, unit conversion, voice control, and cloud integrations.

This rule applies to the `nest` integration as it provides Sensor and Event entities, both of which support device classes.

The `nest` integration **fully follows** this rule:

1.  **Sensor Entities:**
    *   In `homeassistant/components/nest/sensor.py`, the `TemperatureSensor` correctly sets `_attr_device_class = SensorDeviceClass.TEMPERATURE`.
        ```python
        # homeassistant/components/nest/sensor.py
        class TemperatureSensor(SensorBase):
            """Representation of a Temperature Sensor."""

            _attr_device_class = SensorDeviceClass.TEMPERATURE
            _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        ```
    *   The `HumiditySensor` correctly sets `_attr_device_class = SensorDeviceClass.HUMIDITY`.
        ```python
        # homeassistant/components/nest/sensor.py
        class HumiditySensor(SensorBase):
            """Representation of a Humidity Sensor."""

            _attr_device_class = SensorDeviceClass.HUMIDITY
            _attr_native_unit_of_measurement = PERCENTAGE
        ```

2.  **Event Entities:**
    *   In `homeassistant/components/nest/event.py`, `NestTraitEventEntity` uses `NestEventEntityDescription` to define its properties. These descriptions correctly assign device classes:
        *   For doorbell chimes (`EVENT_DOORBELL_CHIME`), `device_class=EventDeviceClass.DOORBELL` is used.
        *   For camera motion/person/sound events (`EVENT_CAMERA_MOTION`), `device_class=EventDeviceClass.MOTION` is used.
        ```python
        # homeassistant/components/nest/event.py
        ENTITY_DESCRIPTIONS = [
            NestEventEntityDescription(
                key=EVENT_DOORBELL_CHIME,
                translation_key="chime",
                device_class=EventDeviceClass.DOORBELL, # Correct
                event_types=[EVENT_DOORBELL_CHIME],
                trait_types=[TraitType.DOORBELL_CHIME],
                api_event_types=[EventType.DOORBELL_CHIME],
            ),
            NestEventEntityDescription(
                key=EVENT_CAMERA_MOTION,
                translation_key="motion",
                device_class=EventDeviceClass.MOTION, # Correct
                event_types=[EVENT_CAMERA_MOTION, EVENT_CAMERA_PERSON, EVENT_CAMERA_SOUND],
                # ...
            ),
        ]
        ```

3.  **Climate and Camera Entities:**
    *   The `ThermostatEntity` (in `climate.py`) and `NestRTSPEntity`/`NestWebRTCEntity` (in `camera.py`) do not set a `_attr_device_class`. This is appropriate because the base Home Assistant `ClimateEntity` and `CameraEntity` types do not have a standard `device_class` attribute in the same way that Sensor, Binary Sensor, or Event entities do. The rule specifies using device classes "where possible," and for these entity platforms, it is not a standard or applicable attribute. The list of available device classes in Home Assistant documentation is primarily for entity types like `binary_sensor`, `cover`, `sensor`, `switch`, and `event`.

The `nest` integration does not define any `binary_sensor` entities, which are another common type that uses device classes.

Therefore, all applicable entities within the `nest` integration correctly utilize device classes.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:08:35. Prompt tokens: 32342, Output tokens: 939, Total tokens: 36571_
