# jewish_calendar: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `appropriate-polling` rule applies to this integration, specifically to its sensor entities. The integration currently does NOT fully follow the rule.

The `jewish_calendar` integration provides two types of entities:
1.  **Binary Sensors** (in `homeassistant/components/jewish_calendar/binary_sensor.py`): These entities correctly set `_attr_should_poll = False` and manage their own state updates using `async_track_point_in_time`. They schedule updates precisely when their state might change (e.g., at sunrise, candle lighting, Havdalah). This is an efficient, event-driven approach and is not the concern for this rule.

2.  **Sensors** (in `homeassistant/components/jewish_calendar/sensor.py`): These entities (e.g., Hebrew date, weekly portion, Zmanim times) are derived from `JewishCalendarBaseSensor`.
    *   `JewishCalendarBaseSensor` does not explicitly set `_attr_should_poll`. For `SensorEntity`, `should_poll` defaults to `True`. This means Home Assistant will attempt to poll these sensor entities.
    *   The platform module (`sensor.py`) does not define a `SCAN_INTERVAL` constant.
    *   The `JewishCalendarBaseSensor` class has a method `async_update_data()` which performs the necessary calculations. This method is called once via `async_added_to_hass()`. However, `JewishCalendarBaseSensor` does not implement the `async_update()` method, which is the method Home Assistant's polling mechanism calls. The default `Entity.async_update()` is a no-op.
    *   Consequently, these sensor entities load their state once when added to Home Assistant and then likely **do not update periodically**, leading to stale data as time progresses (e.g., the Hebrew date sensor would not change after sunset or midnight).

This setup means:
*   The sensors are configured to be polled by Home Assistant (due to `should_poll` defaulting to `True`).
*   If they *were* updating via polling (e.g., if `async_update_data` was named `async_update`), they would be polled at Home Assistant's default interval (e.g., every 30 or 60 seconds) because no `SCAN_INTERVAL` is set. This default interval is not appropriate for data that changes, at most, a few times a day (midnight, sunset, nightfall). This would lead to excessive recalculations by the `hdate` library.
*   As it stands, they are polled, but the poll does nothing, so their data becomes stale. This is a functional issue that also relates to not having a proper, appropriately timed update mechanism.

To comply with the `appropriate-polling` rule, these sensor entities need a mechanism for periodic updates that occurs at a sensible frequency, balancing data freshness with computational cost. The current (lack of) update mechanism for sensors does not meet this requirement.

## Suggestions

To make the `jewish_calendar` sensor entities compliant with the `appropriate-polling` rule and ensure their data remains up-to-date, the recommended approach is to implement a `DataUpdateCoordinator`.

1.  **Implement a `DataUpdateCoordinator`**:
    *   Create a coordinator class (e.g., `JewishCalendarCoordinator`) in `__init__.py` or a new `coordinator.py` file.
    *   This coordinator will be responsible for periodically fetching/calculating the shared calendar data.
    *   The `_async_update_data` method of the coordinator should contain the logic currently in `JewishCalendarBaseSensor.async_update_data()`:
        ```python
        # In your new coordinator class
        async def _async_update_data(self):
            """Fetch and calculate Jewish calendar data."""
            now = dt_util.now()
            # Perform calculations for HDateInfo, Zmanim as in JewishCalendarBaseSensor.async_update_data()
            # Store results in self.data for entities to access
            # Example:
            # today = now.date()
            # event_date = get_astral_event_date(self.hass, SUN_EVENT_SUNSET, today)
            # ... (rest of the logic from async_update_data to calculate daytime_date, after_shkia_date, etc.)
            # return JewishCalendarDataResults(daytime_date, after_shkia_date, after_tzais_date, today_times)

            # Ensure self.hass.data[DOMAIN][self.config_entry.entry_id].runtime_data.location, etc. are accessible
            # or pass necessary parts of JewishCalendarData (like location, diaspora settings) to the coordinator.
            # For simplicity, the JewishCalendarData object itself could be updated by the coordinator.
            # Let's assume self.jewish_calendar_data is an instance of JewishCalendarData
            
            # Simplified conceptual logic:
            location = self.jewish_calendar_data.location # Assuming coordinator has access to this
            diaspora = self.jewish_calendar_data.diaspora
            
            # ... (calculations as in original async_update_data) ...
            
            daytime_date = HDateInfo(today, diaspora=diaspora)
            # ... calculation of after_shkia_date, after_tzais_date, today_times ...

            return JewishCalendarDataResults(
                daytime_date, after_shkia_date, after_tzais_date, today_times
            )

        ```
    *   Initialize this coordinator in `async_setup_entry` (in `__init__.py`):
        ```python
        # __init__.py
        from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
        from datetime import timedelta
        # ... other imports ...

        # Example update interval - adjust as needed
        SCAN_INTERVAL_COORDINATOR = timedelta(minutes=15) 

        async def async_setup_entry(
            hass: HomeAssistant, config_entry: JewishCalendarConfigEntry
        ) -> bool:
            # ... (existing setup for language, diaspora, location, etc.) ...

            # Store the core data object (location, settings)
            # This object is already being created: config_entry.runtime_data
            
            coordinator = DataUpdateCoordinator(
                hass,
                _LOGGER,
                name=DOMAIN,
                update_method= # assign the coordinator's _async_update_data method here,
                               # ensuring it has access to config_entry.runtime_data for parameters
                update_interval=SCAN_INTERVAL_COORDINATOR,
            )
            # Store the coordinator on the config_entry or hass.data
            config_entry.runtime_data.coordinator = coordinator # Or a more structured approach

            # Initial data load
            await coordinator.async_config_entry_first_refresh()
            
            # Forward to platforms
            await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
            # ... (rest of async_setup_entry) ...
            return True
        ```
        The `update_method` for the coordinator will need access to the `JewishCalendarData` instance (currently `config_entry.runtime_data`) to get location, diaspora settings, etc. This might involve passing `config_entry.runtime_data` to the coordinator's constructor or making its `_async_update_data` a method of an object that has this data.

        An `update_interval` of `timedelta(minutes=15)` or `timedelta(minutes=30)` is suggested. This is significantly less frequent than default polling but frequent enough to update sensor states reasonably promptly after daily transitions (like sunset or nightfall, which affect the Hebrew date and some Zmanim interpretations). The `hdate` calculations are purely computational, so this interval balances freshness with CPU load.

2.  **Refactor Sensor Entities to Use the Coordinator**:
    *   Modify `JewishCalendarBaseSensor` (and thus its subclasses `JewishCalendarSensor`, `JewishCalendarTimeSensor`) in `sensor.py` to inherit from `CoordinatorEntity`.
    *   Remove the `async_update_data` method from `JewishCalendarBaseSensor`.
    *   The sensors will get their data from `self.coordinator.data`.
    *   In `sensor.py`'s `async_setup_entry`, retrieve the coordinator and pass it to the sensor entities.

    ```python
    # sensor.py
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
    # ... other imports ...

    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: JewishCalendarConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up the Jewish calendar sensors."""
        # Retrieve the coordinator, assuming it's stored in config_entry.runtime_data
        coordinator = config_entry.runtime_data.coordinator 

        sensors: list[JewishCalendarBaseSensor] = [
            JewishCalendarSensor(config_entry, coordinator, description) for description in INFO_SENSORS
        ]
        sensors.extend(
            JewishCalendarTimeSensor(config_entry, coordinator, description)
            for description in TIME_SENSORS
        )
        async_add_entities(sensors)

    class JewishCalendarBaseSensor(CoordinatorEntity, JewishCalendarEntity, SensorEntity): # Inherit CoordinatorEntity
        _attr_entity_category = EntityCategory.DIAGNOSTIC
        # _attr_should_poll = False # Implicitly False when using CoordinatorEntity

        def __init__(
            self,
            config_entry: JewishCalendarConfigEntry,
            coordinator: DataUpdateCoordinator, # Add coordinator parameter
            description: EntityDescription,
        ) -> None:
            """Initialize a Jewish Calendar entity."""
            super().__init__(coordinator, description) # Pass coordinator to CoordinatorEntity
            # Initialize JewishCalendarEntity parts - may need adjustment
            # self.entity_description = description (already done by CoordinatorEntity if description is passed)
            # self._attr_unique_id = f"{config_entry.entry_id}-{description.key}" (done by JewishCalendarEntity)
            # self._attr_device_info = ... (done by JewishCalendarEntity)
            # self.data = config_entry.runtime_data (access data via self.coordinator.data)
            
            # Call JewishCalendarEntity's __init__ appropriately
            JewishCalendarEntity.__init__(self, config_entry, description)
            # Note: CoordinatorEntity also has an __init__ that takes the description.
            # The MRO and __init__ calls need to be handled carefully.
            # A common pattern:
            # super(CoordinatorEntity, self).__init__(coordinator) # Initialize CoordinatorEntity
            # JewishCalendarEntity.__init__(self, config_entry, description) # Initialize your base
            # self.entity_description = description # If not handled by superclasses

        # Remove async_added_to_hass and async_update_data if their logic is moved to coordinator

        # Native_value and extra_state_attributes will now use self.coordinator.data
        # For example, in JewishCalendarSensor:
        # @property
        # def native_value(self) -> str | int | dt.datetime | None:
        #     if self.coordinator.data is None: # Check if coordinator data is available
        #         return None
        #     return self.entity_description.value_fn(self.coordinator.data)
    ```

By implementing these changes:
*   Data calculations are centralized and performed once per interval.
*   The update frequency is explicitly defined and more appropriate for the nature of the data.
*   Sensor entities will correctly update their states periodically.
*   The integration will comply with the `appropriate-polling` rule.

_Created at 2025-05-29 08:03:09. Prompt tokens: 13620, Output tokens: 2768, Total tokens: 23498_
