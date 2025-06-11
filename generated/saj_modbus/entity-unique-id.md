# saj_modbus: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                   |

## Overview

The `entity-unique-id` rule requires that all entities created by an integration have a unique ID. This is crucial for allowing users to customize entities and for Home Assistant to track them across restarts.

The `saj_modbus` integration creates `sensor` and `number` entities, so this rule is applicable. The integration correctly implements unique IDs for all its entities.

The implementation can be seen in the entity platform files:

1.  **Sensor Entities (`sensor.py`)**:
    The `SajSensor` class (which is the base for `SajCounterSensor` as well) correctly defines the `unique_id` property. The ID is a combination of the user-configured device name and a static key from the entity description, ensuring uniqueness for each sensor per device.

    ```python
    # homeassistant/components/saj_modbus/sensor.py
    class SajSensor(CoordinatorEntity, SensorEntity):
        # ...
        @property
        def unique_id(self) -> str | None:
            """Return unique ID fro sensor."""
            return f"{self._platform_name}_{self.entity_description.key}"
    ```

2.  **Number Entities (`number.py`)**:
    The `SajNumber` class correctly sets the `_attr_unique_id` attribute in its initializer, which is the recommended approach. The structure of the ID is the same as for sensors, guaranteeing uniqueness.

    ```python
    # homeassistant/components/saj_modbus/number.py
    class SajNumber(CoordinatorEntity, NumberEntity):
        def __init__(
            self,
            platform_name: str,
            hub: SAJModbusHub,
            device_info,
            description: SajModbusNumberEntityDescription,
        ):
            """Initialize the sensor."""
            self._platform_name = platform_name
            self._attr_device_info = device_info
            self._attr_unique_id = f"{platform_name}_{description.key}"
            self.entity_description: SajModbusNumberEntityDescription = description

            super().__init__(coordinator=hub)
    ```

Both implementations correctly ensure that every entity will have a stable and unique ID within the Home Assistant instance. Therefore, the integration fully complies with this rule.

## Suggestions

No suggestions needed.

---

_Created at 2025-06-11 21:32:47. Prompt tokens: 16572, Output tokens: 632, Total tokens: 18875._

_AI can be wrong. Always verify the report and the code against the rule._
