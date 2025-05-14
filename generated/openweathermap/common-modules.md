# openweathermap: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule requires that common patterns like data update coordinators and base entities be placed in designated files, specifically `coordinator.py` for coordinators and `entity.py` for base entities, to enhance consistency and maintainability.

This rule applies to the `openweathermap` integration because:
1.  It utilizes a `DataUpdateCoordinator` for managing data fetching.
2.  It provides multiple entity platforms (sensor and weather), presenting an opportunity for a shared base entity class to reduce code duplication.

**Assessment:**

*   **Coordinator (`coordinator.py`):**
    The integration **follows** this part of the rule.
    *   The `WeatherUpdateCoordinator` class, which inherits from `DataUpdateCoordinator`, is correctly defined in `homeassistant/components/openweathermap/coordinator.py`.
    *   This coordinator is used in `__init__.py` to manage weather data updates.

*   **Base Entity (`entity.py`):**
    The integration currently **does NOT follow** this part of the rule.
    *   There is no `homeassistant/components/openweathermap/entity.py` file.
    *   The `sensor.py` file defines an `AbstractOpenWeatherMapSensor` class (see `homeassistant/components/openweathermap/sensor.py`, lines 85-119). While this class serves as a base for `OpenWeatherMapSensor` entities, it is specific to the sensor platform and not a shared base entity across different platforms (like sensor and weather).
    *   There is duplicated logic and common attributes that could be consolidated into a shared base entity. For instance:
        *   Both `AbstractOpenWeatherMapSensor` (in `sensor.py`) and `OpenWeatherMapWeather` (in `weather.py`) set `_attr_attribution = ATTRIBUTION`.
        *   Both entities construct a `DeviceInfo` object with similar parameters (`manufacturer`, `name`, `entry_type`, `identifiers` based on the config entry unique ID). This setup is done in `AbstractOpenWeatherMapSensor.__init__` (lines 99-106 in `sensor.py`) and `OpenWeatherMapWeather.__init__` (lines 70-75 in `weather.py`).
    *   A common base entity class, inheriting from `CoordinatorEntity` as per the rule's example, could be created in `entity.py` to centralize these common properties and behaviors.

Due to the absence of a common base entity in `entity.py` to handle shared logic across its sensor and weather platforms, the integration does not fully comply with the `common-modules` rule.

## Suggestions

To make the `openweathermap` integration compliant with the `common-modules` rule regarding base entities, the following changes are recommended:

1.  **Create `entity.py`:**
    Add a new file: `homeassistant/components/openweathermap/entity.py`.

2.  **Define a Common Base Entity:**
    In the new `entity.py`, define a base class, for example, `OpenWeatherMapEntity`, that inherits from `CoordinatorEntity`. This class should handle the common setup for all OpenWeatherMap entities.

    ```python
    # homeassistant/components/openweathermap/entity.py
    from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
    from homeassistant.helpers.update_coordinator import CoordinatorEntity

    from .const import ATTRIBUTION, DOMAIN, MANUFACTURER
    from .coordinator import WeatherUpdateCoordinator

    class OpenWeatherMapEntity(CoordinatorEntity[WeatherUpdateCoordinator]):
        """Base class for OpenWeatherMap entities."""

        _attr_attribution = ATTRIBUTION
        _attr_has_entity_name = True  # Common to both sensor and weather entities

        def __init__(
            self,
            coordinator: WeatherUpdateCoordinator,
            entry_name: str,  # Device name (from config entry's name)
            config_entry_unique_id: str,  # Config entry unique_id for device identification
        ) -> None:
            """Initialize the OpenWeatherMap entity."""
            super().__init__(coordinator)
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, config_entry_unique_id)},
                name=entry_name,
                manufacturer=MANUFACTURER,
                entry_type=DeviceEntryType.SERVICE,
            )
    ```

3.  **Refactor Sensor Entities (`sensor.py`):**
    *   Modify `AbstractOpenWeatherMapSensor` to inherit from the new `OpenWeatherMapEntity` and `SensorEntity`.
    *   Update its `__init__` method to call the parent `OpenWeatherMapEntity`'s constructor and remove redundant attribute settings.

    ```python
    # homeassistant/components/openweathermap/sensor.py
    # ... other imports ...
    from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
    from .entity import OpenWeatherMapEntity # New import
    from .coordinator import WeatherUpdateCoordinator

    # class AbstractOpenWeatherMapSensor(SensorEntity): # Old
    class AbstractOpenWeatherMapSensor(OpenWeatherMapEntity, SensorEntity): # New
        """Abstract class for an OpenWeatherMap sensor."""

        # _attr_attribution, _attr_has_entity_name, and DeviceInfo are now handled by OpenWeatherMapEntity
        # _attr_should_poll = False is handled by CoordinatorEntity (via OpenWeatherMapEntity)

        def __init__(
            self,
            coordinator: WeatherUpdateCoordinator, # Added coordinator as first param
            entry_name: str, # Corresponds to 'name' in original call
            config_entry_unique_id: str, # Corresponds to 'unique_id' in original call
            description: SensorEntityDescription,
        ) -> None:
            """Initialize the sensor."""
            # Call OpenWeatherMapEntity's __init__
            super().__init__(coordinator, entry_name, config_entry_unique_id)
            # SensorEntity specific setup
            self.entity_description = description
            self._attr_unique_id = f"{config_entry_unique_id}-{description.key}"

        # The 'available' property and 'async_added_to_hass' are inherited from OpenWeatherMapEntity (via CoordinatorEntity)
        # The 'async_update' method might need review; CoordinatorEntity typically doesn't require it for state updates.

    class OpenWeatherMapSensor(AbstractOpenWeatherMapSensor):
        """Implementation of an OpenWeatherMap sensor."""

        # No changes needed here if AbstractOpenWeatherMapSensor is correctly refactored
        # The __init__ signature will be passed from async_setup_entry up to AbstractOpenWeatherMapSensor

        @property
        def native_value(self) -> StateType:
            """Return the state of the device."""
            return self._coordinator.data[ATTR_API_CURRENT].get(self.entity_description.key)

    # In async_setup_entry(hass, config_entry, async_add_entities):
    # ...
    # name = domain_data.name
    # unique_id_val = config_entry.unique_id
    # weather_coordinator = domain_data.coordinator
    # ...
    # async_add_entities(
    #     OpenWeatherMapSensor(
    #         weather_coordinator, # Pass coordinator first
    #         name,
    #         unique_id_val,
    #         description,
    #     )
    #     for description in WEATHER_SENSOR_TYPES
    # )
    ```

4.  **Refactor Weather Entity (`weather.py`):**
    *   Modify `OpenWeatherMapWeather` to inherit from the new `OpenWeatherMapEntity` and `WeatherEntity`. This replaces `SingleCoordinatorWeatherEntity` while ensuring `CoordinatorEntity` and `WeatherEntity` functionalities are present.
    *   Update its `__init__` method to call the parent `OpenWeatherMapEntity`'s constructor.

    ```python
    # homeassistant/components/openweathermap/weather.py
    # ... other imports ...
    from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature # Removed SingleCoordinatorWeatherEntity
    from .entity import OpenWeatherMapEntity # New import
    from .coordinator import WeatherUpdateCoordinator

    # class OpenWeatherMapWeather(SingleCoordinatorWeatherEntity[WeatherUpdateCoordinator]): # Old
    class OpenWeatherMapWeather(OpenWeatherMapEntity, WeatherEntity): # New
        """Implementation of an OpenWeatherMap weather entity."""

        # _attr_attribution, _attr_has_entity_name, and DeviceInfo are now handled by OpenWeatherMapEntity
        # _attr_should_poll = False is handled by CoordinatorEntity (via OpenWeatherMapEntity)
        _attr_name = None # To use entity description for name part if applicable, or rely on device name

        _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
        # ... other native unit attributes remain ...

        def __init__(
            self,
            coordinator: WeatherUpdateCoordinator, # Pass coordinator
            entry_name: str, # Corresponds to 'name' in original call
            config_entry_unique_id: str, # Corresponds to 'unique_id' in original call
            mode: str,
        ) -> None:
            """Initialize the weather entity."""
            super().__init__(coordinator, entry_name, config_entry_unique_id) # Call OpenWeatherMapEntity.__init__
            # WeatherEntity specific setup
            self._attr_unique_id = config_entry_unique_id # Weather entity uses device unique_id
            self.mode = mode

            if mode == OWM_MODE_V30:
                self._attr_supported_features = (
                    WeatherEntityFeature.FORECAST_DAILY
                    | WeatherEntityFeature.FORECAST_HOURLY
                )
            elif mode == OWM_MODE_FREE_FORECAST:
                self._attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY
        
        # ... rest of the properties (condition, native_temperature, etc.) and forecast methods ...
        # Ensure they correctly access self.coordinator.data as before.

    # In async_setup_entry(hass, config_entry, async_add_entities):
    # ...
    # name = domain_data.name
    # mode = domain_data.mode
    # weather_coordinator = domain_data.coordinator
    # unique_id_val = f"{config_entry.unique_id}"
    # owm_weather = OpenWeatherMapWeather(weather_coordinator, name, unique_id_val, mode, weather_coordinator) # Original call was (name, unique_id, mode, weather_coordinator)
    # Updated call:
    # owm_weather = OpenWeatherMapWeather(weather_coordinator, name, unique_id_val, mode)
    ```

By implementing these suggestions, the `openweathermap` integration will centralize common entity logic in `entity.py`, adhering to the `common-modules` rule, improving code organization, and reducing duplication.

_Created at 2025-05-14 15:14:06. Prompt tokens: 13730, Output tokens: 2575, Total tokens: 24046_
