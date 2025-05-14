# openweathermap: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `appropriate-polling` rule requires that polling integrations set a polling interval that is suitable for the majority of users, balancing data freshness with responsible resource use (e.g., API call limits, system load).

This rule applies to the `openweathermap` integration because its `manifest.json` declares `"iot_class": "cloud_polling"`, indicating it retrieves data by polling a cloud service.

The integration **follows** this rule.

1.  **Polling Mechanism**: The integration uses a `DataUpdateCoordinator` (`WeatherUpdateCoordinator`) to manage data fetching, which is the recommended approach for polling. This is defined in `homeassistant/components/openweathermap/coordinator.py`.

2.  **Polling Interval**:
    The `WeatherUpdateCoordinator` sets a specific update interval. In `homeassistant/components/openweathermap/coordinator.py`, we find:
    ```python
    WEATHER_UPDATE_INTERVAL = timedelta(minutes=10)

    class WeatherUpdateCoordinator(DataUpdateCoordinator):
        # ...
        def __init__(
            self,
            # ...
        ) -> None:
            # ...
            super().__init__(
                hass,
                _LOGGER,
                config_entry=config_entry,
                name=DOMAIN,
                update_interval=WEATHER_UPDATE_INTERVAL, # The interval is set here
            )
    ```
    The `update_interval` is explicitly set to `WEATHER_UPDATE_INTERVAL`, which is `timedelta(minutes=10)`.

3.  **Appropriateness of the Interval**: A 10-minute polling interval for OpenWeatherMap data is generally appropriate:
    *   **Data Update Frequency**: OpenWeatherMap itself states that its current weather data is updated approximately every 10 minutes. Polling more frequently would likely yield no new data for current conditions and consume API calls unnecessarily. Forecast data is typically updated less frequently (e.g., hourly).
    *   **API Limits**: Cloud weather services, including OpenWeatherMap, often have API call limits, especially for free tiers. A 10-minute interval (144 calls per day per configured location) is considerate of these limits, ensuring most users stay within free tier allowances while receiving reasonably up-to-date information.
    *   **User Experience**: For weather data, updates every 10 minutes are sufficient for typical use cases like displaying current conditions or short-term forecasts. Users requiring more frequent updates for specific needs can often customize this through Home Assistant's global polling interval settings for an integration, as mentioned in the rule's documentation.
    *   **Entity Polling**: Sensor and weather entities within the integration correctly set `_attr_should_poll = False` (e.g., in `sensor.py`'s `AbstractOpenWeatherMapSensor` and `weather.py`'s `OpenWeatherMapWeather`), ensuring they rely on the coordinator for updates rather than polling independently. This adheres to best practices when using a `DataUpdateCoordinator`.

Given these points, the `openweathermap` integration implements polling correctly via a `DataUpdateCoordinator` and uses a 10-minute interval, which is well-suited for the nature and update frequency of the OpenWeatherMap service.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:12:25. Prompt tokens: 13969, Output tokens: 807, Total tokens: 17031_
