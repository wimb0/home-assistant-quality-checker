# jewish_calendar: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **todo**                                                                 |

## Overview

The `common-modules` rule applies to the `jewish_calendar` integration as it provides multiple entities and involves data that changes over time, which are typical scenarios for using base entities and data update coordinators.

The integration partially follows the rule:
1.  **Base Entity**: The integration correctly uses a base entity class, `JewishCalendarEntity`, which is defined in `homeassistant/components/jewish_calendar/entity.py`. This aligns with the rule's requirement to place base entities in `entity.py`. This base class is inherited by `JewishCalendarBaseSensor` (in `sensor.py`) and `JewishCalendarBinarySensor` (in `binary_sensor.py`).

2.  **Coordinator for Data Fetching**: The integration does **not** follow the common pattern of using a central data update coordinator (e.g., `DataUpdateCoordinator`) located in a `coordinator.py` file.
    *   Currently, data essential for sensor states (like Hebrew dates and Zmanim) is calculated within the `JewishCalendarBaseSensor.async_update_data` method in `homeassistant/components/jewish_calendar/sensor.py`. This method updates a shared `JewishCalendarData.results` object stored in `config_entry.runtime_data`.
        ```python
        # homeassistant/components/jewish_calendar/sensor.py
        class JewishCalendarBaseSensor(JewishCalendarEntity, SensorEntity):
            # ...
            async def async_update_data(self) -> None:
                # ...
                self.data.results = JewishCalendarDataResults(...)
        ```
    *   Binary sensors, defined in `homeassistant/components/jewish_calendar/binary_sensor.py`, perform their own calculations for Zmanim by directly calling the `make_zmanim` method inherited from `JewishCalendarEntity`. They do not utilize the `Zmanim` object potentially calculated and stored by the sensor update logic in `self.data.results`.
        ```python
        # homeassistant/components/jewish_calendar/binary_sensor.py
        class JewishCalendarBinarySensor(JewishCalendarEntity, BinarySensorEntity):
            # ...
            @property
            def is_on(self) -> bool:
                zmanim = self.make_zmanim(dt.date.today()) # Independent calculation
                return self.entity_description.is_on(zmanim, dt_util.now())
        ```
    *   This approach lacks a single, centralized component responsible for fetching, processing, and distributing updated data to all relevant entities. The rule promotes placing such centralized data fetching logic (the "coordinator") in a `coordinator.py` file to improve consistency and maintainability across integrations.

Because the integration involves time-sensitive data calculations that would benefit from a centralized coordinator pattern, and this pattern is not implemented (nor is there a `coordinator.py` file), the integration does not fully adhere to the `common-modules` rule.

## Suggestions

To make the `jewish_calendar` integration compliant with the `common-modules` rule and improve its architecture, the following changes are recommended:

1.  **Create `coordinator.py`:**
    *   Introduce a new file `homeassistant/components/jewish_calendar/coordinator.py`.
    *   Define a `JewishCalendarCoordinator` class in this file, inheriting from `homeassistant.helpers.update_coordinator.DataUpdateCoordinator`.
        ```python
        # Example structure for coordinator.py
        from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
        from homeassistant.core import HomeAssistant
        import logging
        from datetime import timedelta

        from .const import DOMAIN
        # Import necessary data structures like JewishCalendarDataResults, HDateInfo, Zmanim
        # (these might need to be moved or made accessible here)

        _LOGGER = logging.getLogger(__name__)

        class JewishCalendarCoordinator(DataUpdateCoordinator[JewishCalendarDataResults]): # Or a similar data type
            """Class to manage fetching Jewish calendar data."""

            def __init__(self, hass: HomeAssistant, config_entry_data: JewishCalendarData): # Pass necessary config
                """Initialize coordinator."""
                self.config_data = config_entry_data # Store original config data if needed
                super().__init__(
                    hass,
                    _LOGGER,
                    name=DOMAIN,
                    update_interval=timedelta(minutes=30), # Adjust as appropriate, or use custom scheduling
                )

            async def _async_update_data(self) -> JewishCalendarDataResults:
                """Fetch and process data from the hdate library."""
                try:
                    # This logic would be similar to what's currently in
                    # JewishCalendarBaseSensor.async_update_data()
                    # It should calculate HDateInfo, Zmanim, etc.
                    # and return an instance of JewishCalendarDataResults or a similar structure.
                    # Example:
                    # now = dt_util.now()
                    # today = now.date()
                    # zmanim = Zmanim(date=today, location=self.config_data.location, ...)
                    # daytime_date = HDateInfo(today, diaspora=self.config_data.diaspora)
                    # ...
                    # return JewishCalendarDataResults(daytime_date, after_shkia_date, after_tzais_date, zmanim)
                    pass # Replace with actual implementation
                except Exception as err:
                    raise UpdateFailed(f"Error communicating with API: {err}") from err
        ```

2.  **Update `__init__.py`:**
    *   In `async_setup_entry`, instantiate and set up the `JewishCalendarCoordinator`.
    *   Store the coordinator instance on the `config_entry.runtime_data` (or a new dedicated field like `config_entry.coordinator`).
    *   Perform an initial data refresh using `await coordinator.async_config_entry_first_refresh()`.

3.  **Refactor `entity.py`:**
    *   Modify `JewishCalendarEntity` to inherit from `homeassistant.helpers.update_coordinator.CoordinatorEntity` and accept the coordinator instance.
        ```python
        # Example change in entity.py
        from homeassistant.helpers.update_coordinator import CoordinatorEntity

        # class JewishCalendarEntity(Entity): # Old
        class JewishCalendarEntity(CoordinatorEntity[JewishCalendarCoordinator]): # New
            # ...
            def __init__(
                self,
                coordinator: JewishCalendarCoordinator, # Pass coordinator
                config_entry: JewishCalendarConfigEntry, # Keep if needed for other things
                description: EntityDescription,
            ) -> None:
                super().__init__(coordinator) # Call super with coordinator
                # ... existing __init__ logic ...
                # self.data is now self.coordinator.data for fetched results
                # The original self.data (JewishCalendarData) might still be needed for static config
                # and can be passed separately or accessed via coordinator if stored there.
        ```
    *   The data classes `JewishCalendarData` and `JewishCalendarDataResults` might be better placed in `coordinator.py` or a new `data.py` file if they primarily serve the coordinator.

4.  **Update Sensor Entities (`sensor.py`):**
    *   Remove the `async_update_data` method from `JewishCalendarBaseSensor`. Updates will be handled by the coordinator.
    *   Sensors should derive their state (`native_value`, `extra_state_attributes`) from `self.coordinator.data` (which would hold the `JewishCalendarDataResults` instance).
        ```python
        # Example change in sensor.py
        @property
        def native_value(self) -> str | int | dt.datetime | None:
            if self.coordinator.data is None: # Data from coordinator
                return None
            return self.entity_description.value_fn(self.coordinator.data)
        ```

5.  **Update Binary Sensor Entities (`binary_sensor.py`):**
    *   Binary sensors should also derive their state from `self.coordinator.data`.
    *   The `is_on` property should use `self.coordinator.data.zmanim` (or similar from the coordinator's data) instead of calling `make_zmanim` directly.
        ```python
        # Example change in binary_sensor.py
        @property
        def is_on(self) -> bool:
            if self.coordinator.data is None or self.coordinator.data.zmanim is None:
                return False # Or handle appropriately
            # Use self.coordinator.data.zmanim instead of self.make_zmanim()
            return self.entity_description.is_on(self.coordinator.data.zmanim, dt_util.now())
        ```
    *   The custom update scheduling (`_schedule_update`, `_update`) in `JewishCalendarBinarySensor` might be simplified or removed if the coordinator's update interval is sufficient or if binary sensors can rely on the standard `CoordinatorEntity` update mechanism. If very precise timing for binary sensor updates is needed around specific zmanim, `async_track_point_in_time` could still be used, but it should be coordinated with or use data from the central coordinator.

By implementing these suggestions, the data fetching and processing logic will be centralized in `JewishCalendarCoordinator` within `coordinator.py`. All entities will then subscribe to this coordinator for data, ensuring consistency, reducing redundant calculations, and aligning the integration with Home Assistant's common architectural patterns as outlined by the `common-modules` rule.

_Created at 2025-05-29 08:04:44. Prompt tokens: 13381, Output tokens: 2244, Total tokens: 21840_
