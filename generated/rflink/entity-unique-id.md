# rflink: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [rflink](https://www.home-assistant.io/integrations/rflink/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unique-id` rule requires all entities to have a unique ID, which is essential for the entity registry to track and manage entities, allowing user customizations. This rule applies to the `rflink` integration as it creates various entities (binary sensors, covers, lights, sensors, switches).

The `rflink` integration generally attempts to set a unique ID for its entities. The base class `RflinkDevice` (in `homeassistant/components/rflink/entity.py`) initializes `self._attr_unique_id = device_id` in its `__init__` method.

For most entity types and configurations, this approach works:
*   **Manually Configured Entities (binary_sensor, cover, light, sensor, switch):** When entities are defined in `configuration.yaml`, the `device_id` passed to the entity constructor is the key specified in the YAML configuration (e.g., `my_living_room_light` or `weather_station_temperature`). These keys are inherently unique per entity definition, so `_attr_unique_id` becomes unique.
*   **Automatically Added Lights:** When `automatic_add` is enabled for lights, a new light entity is created based on an RFLink event. The `device_id` used is `event[EVENT_KEY_ID]` from the RFLink packet. Typically, one RFLink device ID corresponds to a single light entity (e.g., a specific wall switch). Thus, `_attr_unique_id = event[EVENT_KEY_ID]` is unique for these light entities.
*   **Switches, Covers, Binary Sensors (from configuration):** These are configured manually, so the `device_id` (YAML key) ensures uniqueness for `_attr_unique_id`.

However, the integration does **NOT** fully follow the rule for **automatically added sensors**.
When `automatic_add` is enabled for sensors (in `sensor.py`), multiple sensor entities can be created from the same physical RFLink device reporting different types of values (e.g., temperature and humidity). These events share the same base `event[EVENT_KEY_ID]` but differ in `event[EVENT_KEY_SENSOR]`.

The current implementation for automatically added sensors is:
```python
# homeassistant/components/rflink/sensor.py
async def add_new_device(event):
    device_id = event[EVENT_KEY_ID]  # e.g., "weatherstation_01"
    sensor_type = event[EVENT_KEY_SENSOR] # e.g., "TEMP" or "HUM"
    # ...
    device = RflinkSensor(
        device_id,
        sensor_type,
        # ...
    )
    # ...

# homeassistant/components/rflink/entity.py
class RflinkDevice(Entity):
    def __init__(self, device_id, ...):
        self._device_id = device_id
        self._attr_unique_id = device_id # This becomes "weatherstation_01"
        # ...

# homeassistant/components/rflink/sensor.py
class RflinkSensor(RflinkDevice, SensorEntity):
    def __init__(self, device_id: str, sensor_type: str, ...):
        self._sensor_type = sensor_type
        super().__init__(device_id, ...) # Calls RflinkDevice.__init__
        # _attr_unique_id is now set to the base device_id
```
If a device `weatherstation_01` sends a temperature reading (`sensor_type="TEMP"`) and later a humidity reading (`sensor_type="HUM"`), two `RflinkSensor` instances will be created. Both will have `self._attr_unique_id` set to `"weatherstation_01"`. This results in non-unique IDs for these distinct sensor entities, violating the rule and potentially causing issues in the entity registry.

## Suggestions

To make the `rflink` integration compliant with the `entity-unique-id` rule for automatically discovered sensors, the `_attr_unique_id` for `RflinkSensor` entities needs to incorporate the sensor type to ensure uniqueness when multiple sensor values originate from the same base RFLink device ID.

Modify `RflinkSensor.__init__` in `homeassistant/components/rflink/sensor.py` as follows:

```python
# homeassistant/components/rflink/sensor.py

class RflinkSensor(RflinkDevice, SensorEntity):
    def __init__(
        self,
        device_id: str,  # This is the base RFLink device ID (e.g., "protocol_id123_0")
        sensor_type: str, # This is the specific sensor type (e.g., "TEMP", "HUMIDITY")
        unit_of_measurement: str | None = None,
        initial_event=None,
        **kwargs: Any,
    ) -> None:
        """Handle sensor specific args and super init."""
        self._sensor_type = sensor_type
        self._unit_of_measurement = unit_of_measurement
        if sensor_type in SENSOR_TYPES_DICT:
            self.entity_description = SENSOR_TYPES_DICT[sensor_type]
        elif not unit_of_measurement:
            self._unit_of_measurement = lookup_unit_for_sensor_type(sensor_type)

        # Call the RflinkDevice constructor with the base device_id.
        # This will set self._device_id = device_id and, by default,
        # self._attr_unique_id = device_id.
        super().__init__(device_id, initial_event=initial_event, **kwargs)

        # For RflinkSensor, explicitly override _attr_unique_id to ensure it's
        # unique across different sensor types from the same base RFLink device.
        # self._device_id still holds the base RFLink ID (e.g., "protocol_id123_0").
        # self._sensor_type holds the specific sensor type (e.g., "TEMP").
        # The resulting unique ID could be "protocol_id123_0_temp".
        self._attr_unique_id = f"{self._device_id}_{self._sensor_type.lower()}"
```

**Why this change satisfies the rule:**
*   The `_attr_unique_id` will now be a combination of the base RFLink device ID and the specific sensor type (e.g., `rflink_id_temp`, `rflink_id_humidity`).
*   This ensures that even if a single RFLink physical device reports multiple sensor values (temperature, humidity, etc.), each corresponding Home Assistant sensor entity will have a truly unique identifier.
*   The `self._device_id` attribute (used for internal logic like event lookups) remains the base RFLink ID, preserving existing functionality that relies on it.
*   Other entity types (Light, Switch, Cover, BinarySensor) can continue to use the base `device_id` as their `_attr_unique_id` because they typically represent a single entity per RFLink device ID.

_Created at 2025-05-28 13:29:35. Prompt tokens: 17643, Output tokens: 1709, Total tokens: 26669_
