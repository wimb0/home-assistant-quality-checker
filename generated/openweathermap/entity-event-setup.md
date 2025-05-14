# openweathermap: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-event-setup` rule requires that entities subscribing to events (e.g., from an integration library or, in this case, a `DataUpdateCoordinator`) do so in the `async_added_to_hass` method and unsubscribe in `async_will_remove_from_hass`. The use of `async_on_remove` within `async_added_to_hass` is the recommended way to handle unsubscription.

This rule applies to the `openweathermap` integration because its sensor and weather entities subscribe to updates from a `DataUpdateCoordinator`.

The integration **follows** this rule:

1.  **Sensor Entities (`sensor.py`):**
    The `AbstractOpenWeatherMapSensor` class, which `OpenWeatherMapSensor` inherits from, correctly implements the pattern in its `async_added_to_hass` method:
    ```python
    # homeassistant/components/openweathermap/sensor.py
    class AbstractOpenWeatherMapSensor(SensorEntity):
        # ...
        async def async_added_to_hass(self) -> None:
            """Connect to dispatcher listening for entity data notifications."""
            self.async_on_remove(
                self._coordinator.async_add_listener(self.async_write_ha_state)
            )
    ```
    Here, `self._coordinator.async_add_listener(self.async_write_ha_state)` registers a callback to update the entity's state when the coordinator has new data. The `self.async_on_remove()` helper ensures that the listener is automatically removed when the entity is removed from Home Assistant (during `async_will_remove_from_hass`).

2.  **Weather Entity (`weather.py`):**
    The `OpenWeatherMapWeather` entity inherits from `SingleCoordinatorWeatherEntity`. The `SingleCoordinatorWeatherEntity` class, in turn, inherits from `CoordinatorEntity` (defined in `homeassistant/helpers/update_coordinator.py`). The `CoordinatorEntity` base class already implements this pattern correctly:
    ```python
    # homeassistant/helpers/update_coordinator.py
    class CoordinatorEntity(Entity, Generic[_DataT]):
        # ...
        async def async_added_to_hass(self) -> None:
            """When entity is added to hass."""
            await super().async_added_to_hass()
            self.async_on_remove(
                self.coordinator.async_add_listener(self._handle_coordinator_update)
            )
        # ...
    ```
    Since `OpenWeatherMapWeather` does not override `async_added_to_hass` or `async_will_remove_from_hass`, it benefits from this correct base class implementation.

Both sensor and weather entities in the `openweathermap` integration properly manage their subscription to coordinator updates using the recommended lifecycle methods and helpers, thus adhering to the `entity-event-setup` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:16:24. Prompt tokens: 13984, Output tokens: 763, Total tokens: 16300_
