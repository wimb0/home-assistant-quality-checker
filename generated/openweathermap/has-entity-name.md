# openweathermap: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule requires entities to set `_attr_has_entity_name = True` to improve the consistency of entity naming in Home Assistant. This allows entity names to be constructed by combining the device name and a specific entity aspect, or by using the device name directly for the main feature of a device.

This rule applies to the `openweathermap` integration as it provides sensor and weather entities.

The integration correctly follows this rule:

1.  **Sensor Entities:**
    *   In `homeassistant/components/openweathermap/sensor.py`, the `AbstractOpenWeatherMapSensor` class, which is the base for all sensors provided by this integration, sets `_attr_has_entity_name = True`.
        ```python
        # homeassistant/components/openweathermap/sensor.py
        class AbstractOpenWeatherMapSensor(SensorEntity):
            # ...
            _attr_has_entity_name = True
            # ...
        ```
    *   The `_attr_name` for these sensor entities is implicitly set via the `name` attribute of their `SensorEntityDescription`. For example, a sensor with `description.name = "Temperature"` associated with a device named "My Weather Station" will result in an entity named "My Weather Station Temperature". This is the desired behavior as described by the rule.
    *   The device name itself is passed to `DeviceInfo` within the `AbstractOpenWeatherMapSensor`'s `__init__` method:
        ```python
        # homeassistant/components/openweathermap/sensor.py
        def __init__(
            self,
            name: str, # This is the device name
            unique_id: str,
            description: SensorEntityDescription,
            coordinator: DataUpdateCoordinator,
        ) -> None:
            # ...
            self._attr_device_info = DeviceInfo(
                # ...
                name=name, # Device name
            )
            # self.entity_description.name provides the specific entity name part
        ```

2.  **Weather Entity:**
    *   In `homeassistant/components/openweathermap/weather.py`, the `OpenWeatherMapWeather` class sets `_attr_has_entity_name = True` and `_attr_name = None`.
        ```python
        # homeassistant/components/openweathermap/weather.py
        class OpenWeatherMapWeather(SingleCoordinatorWeatherEntity[WeatherUpdateCoordinator]):
            # ...
            _attr_has_entity_name = True
            _attr_name = None
            # ...
        ```
    *   Setting `_attr_name = None` when `_attr_has_entity_name = True` indicates that this entity represents the main feature of the device. Therefore, its name will be the device name. For a device named "My Weather Station", the weather entity will be named "My Weather Station". This is also the correct implementation according to the rule.
    *   The device name is passed to `DeviceInfo` within the `OpenWeatherMapWeather`'s `__init__` method:
        ```python
        # homeassistant/components/openweathermap/weather.py
        def __init__(
            self,
            name: str, # This is the device name
            unique_id: str,
            mode: str,
            weather_coordinator: WeatherUpdateCoordinator,
        ) -> None:
            # ...
            self._attr_device_info = DeviceInfo(
                # ...
                name=name, # Device name
            )
        ```

Both types of entities provided by the `openweathermap` integration adhere to the `has-entity-name` rule by correctly setting `_attr_has_entity_name` and managing `_attr_name` (or relying on `EntityDescription.name`) to achieve the desired naming convention.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:17:10. Prompt tokens: 13904, Output tokens: 960, Total tokens: 16101_
