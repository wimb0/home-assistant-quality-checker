# openweathermap: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule mandates the use of `ConfigEntry.runtime_data` for storing data that is necessary during the lifetime of a configuration entry but is not persisted to configuration storage. It also promotes the use of a custom typed `ConfigEntry` for type safety and consistency.

The `openweathermap` integration **applies** to this rule because it needs to manage runtime objects such as the API client and the data update coordinator.

The integration **fully follows** this rule.

1.  **Custom Typed `ConfigEntry`**:
    In `homeassistant/components/openweathermap/__init__.py`, a custom typed `ConfigEntry` is defined:
    ```python
    type OpenweathermapConfigEntry = ConfigEntry[OpenweathermapData]
    ```
    This type is then consistently used in function signatures throughout the integration where a `ConfigEntry` object is expected, such as `async_setup_entry`, `async_migrate_entry`, `async_unload_entry`, and in platform setup functions.

2.  **`runtime_data` Structure**:
    A `dataclass` named `OpenweathermapData` is defined to structure the data stored in `runtime_data`:
    ```python
    @dataclass
    class OpenweathermapData:
        """Runtime data definition."""

        name: str
        mode: str
        coordinator: WeatherUpdateCoordinator
    ```

3.  **Storing Data in `runtime_data`**:
    In `async_setup_entry` within `homeassistant/components/openweathermap/__init__.py`, an instance of `OpenweathermapData` (which includes the `WeatherUpdateCoordinator` and other relevant runtime parameters like `name` and `mode`) is assigned to `entry.runtime_data`:
    ```python
    # ...
    owm_client = create_owm_client(api_key, mode, lang=language)
    weather_coordinator = WeatherUpdateCoordinator(hass, entry, owm_client)

    await weather_coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    entry.runtime_data = OpenweathermapData(name, mode, weather_coordinator) # <--- Rule followed
    # ...
    ```
    The `WeatherUpdateCoordinator` itself holds the `owm_client`, which is a prime example of runtime data. While `name` and `mode` are derived from `entry.data` and `entry.options` respectively, their inclusion in the `OpenweathermapData` object for easy access alongside the coordinator is a clean implementation.

4.  **Accessing `runtime_data`**:
    Other parts of the integration, such as `sensor.py` and `weather.py`, correctly access this runtime information via `config_entry.runtime_data`:
    For example, in `homeassistant/components/openweathermap/sensor.py`:
    ```python
    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: OpenweathermapConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up OpenWeatherMap sensor entities based on a config entry."""
        domain_data = config_entry.runtime_data # <--- Accessing runtime_data
        name = domain_data.name
        # ...
        weather_coordinator = domain_data.coordinator
        # ...
    ```

This approach aligns with the rule's intent to provide a consistent and typed way to manage runtime data associated with a config entry.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:17:39. Prompt tokens: 13775, Output tokens: 900, Total tokens: 16607_
