```markdown
# fritzbox: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default) |
| Status | **todo**                                                                 |

## Overview

This rule requires that integrations disable less popular or noisy entities by default to conserve system resources. The `fritzbox` integration creates various entity types, making this rule applicable.

The integration partially follows the rule by disabling the `battery_low` binary sensor, which is marked as `EntityCategory.DIAGNOSTIC`. However, several other sensor entities that are also diagnostic or potentially less popular are not disabled by default.

Specifically, reviewing `homeassistant/components/fritzbox/sensor.py`:

1.  The `battery` sensor (`key="battery"`) is marked with `entity_category=EntityCategory.DIAGNOSTIC` but does not have `entity_registry_enabled_default=False` set in its `FritzSensorEntityDescription`.
2.  All thermostat-related sensors (`comfort_temperature`, `eco_temperature`, `nextchange_temperature`, `nextchange_time`, `nextchange_preset`, `scheduled_preset`) are marked with `entity_category=EntityCategory.DIAGNOSTIC` but do not have `entity_registry_enabled_default=False` set. These provide detailed scheduling information which may not be needed by all users for basic thermostat control.
3.  The `voltage` and `electric_current` power sensors are also candidates for being less popular or noisy, but are enabled by default.

While the `battery_low` binary sensor correctly implements the rule by setting `entity_registry_enabled_default=False` in `homeassistant/components/fritzbox/binary_sensor.py`, the omission for the aforementioned sensor entities means the integration does not fully comply with the requirement to disable less popular/diagnostic entities by default.

## Suggestions

To fully comply with the `entity-disabled-by-default` rule, the following sensor entities, which are diagnostic or potentially less popular, should be disabled by default:

1.  **`battery` sensor:** In `homeassistant/components/fritzbox/sensor.py`, add `entity_registry_enabled_default=False` to the `FritzSensorEntityDescription` for the `battery` key.

    ```python
    FritzSensorEntityDescription(
        key="battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suitable=lambda device: device.battery_level is not None,
        native_value=lambda device: device.battery_level,
        entity_registry_enabled_default=False, # Add this line
    ),
    ```

2.  **Thermostat Diagnostic Sensors:** In `homeassistant/components/fritzbox/sensor.py`, add `entity_registry_enabled_default=False` to the `FritzSensorEntityDescription` for the keys `comfort_temperature`, `eco_temperature`, `nextchange_temperature`, `nextchange_time`, `nextchange_preset`, and `scheduled_preset`.

    ```python
    # Example for comfort_temperature
    FritzSensorEntityDescription(
        key="comfort_temperature",
        translation_key="comfort_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        suitable=suitable_comfort_temperature,
        native_value=lambda device: device.comfort_temperature,
        entity_registry_enabled_default=False, # Add this line
    ),
    # Repeat for eco_temperature, nextchange_temperature, nextchange_time, nextchange_preset, scheduled_preset
    ```

3.  **Consider Power Detail Sensors:** Review if `voltage` and `electric_current` are considered less popular than total energy or power consumption for the average user. If so, they could also be disabled by default following the same pattern.

Implementing these changes will ensure that these less commonly used diagnostic entities are disabled by default, allowing users who need them to enable them manually while reducing resource usage for those who do not.
```

_Created at 2025-05-25 11:36:25. Prompt tokens: 19038, Output tokens: 1025, Total tokens: 22096_
