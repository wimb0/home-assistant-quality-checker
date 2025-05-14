# openweathermap: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unique-id` rule requires that all entities created by an integration have a unique ID. This ID is essential for Home Assistant to track entities across restarts and allow users to customize them (e.g., rename, change area). The unique ID must be unique per integration domain and per platform domain.

This rule applies to the `openweathermap` integration because it creates entities. Specifically, it registers `sensor` and `weather` entities as defined in its `const.py` (`PLATFORMS = [Platform.SENSOR, Platform.WEATHER]`).

The integration correctly follows this rule:

1.  **Config Entry Unique ID:**
    The `config_flow.py` sets a unique ID for each config entry based on latitude and longitude:
    ```python
    # homeassistant/components/openweathermap/config_flow.py
    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        # ...
        latitude = user_input[CONF_LATITUDE]
        longitude = user_input[CONF_LONGITUDE]
        await self.async_set_unique_id(f"{latitude}-{longitude}")
        # ...
    ```
    This ensures that each configured instance of OpenWeatherMap has a distinct base unique ID.

2.  **Sensor Entities:**
    In `sensor.py`, the `AbstractOpenWeatherMapSensor` class, which is the base for all sensor entities created by this integration, constructs its unique ID by appending an entity-specific key to the config entry's unique ID.
    ```python
    # homeassistant/components/openweathermap/sensor.py
    class AbstractOpenWeatherMapSensor(SensorEntity):
        # ...
        def __init__(
            self,
            name: str,
            unique_id: str, # This is config_entry.unique_id
            description: SensorEntityDescription,
            coordinator: DataUpdateCoordinator,
        ) -> None:
            # ...
            self._attr_unique_id = f"{unique_id}-{description.key}"
            # ...
    ```
    The `unique_id` passed to the constructor is the `config_entry.unique_id`. The `description.key` (e.g., `ATTR_API_TEMPERATURE`, `ATTR_API_HUMIDITY`) ensures uniqueness for each sensor type within that config entry. This pattern correctly implements unique IDs for sensor entities.

3.  **Weather Entity:**
    In `weather.py`, the `OpenWeatherMapWeather` entity uses the config entry's unique ID directly as its unique ID.
    ```python
    # homeassistant/components/openweathermap/weather.py
    class OpenWeatherMapWeather(SingleCoordinatorWeatherEntity[WeatherUpdateCoordinator]):
        # ...
        def __init__(
            self,
            name: str,
            unique_id: str, # This is based on config_entry.unique_id
            mode: str,
            weather_coordinator: WeatherUpdateCoordinator,
        ) -> None:
            super().__init__(weather_coordinator)
            self._attr_unique_id = unique_id
            # ...
    ```
    The `unique_id` passed to the constructor is `f"{config_entry.unique_id}"` as set up in `weather.py`'s `async_setup_entry`. Since there is typically one primary weather entity per config entry, using the config entry's unique ID directly is a common and valid approach for ensuring the weather entity's unique ID.

Both sensor and weather entities properly assign `_attr_unique_id`, leveraging the `config_entry.unique_id` and, for sensors, an additional key to ensure uniqueness across all entities provided by the integration.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:16:48. Prompt tokens: 13718, Output tokens: 941, Total tokens: 16029_
