# jewish_calendar: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `entity-unavailable` rule states that if an integration cannot fetch data from a device or service, its entities should be marked as unavailable. This reflects a more accurate state than showing potentially stale data or an error state while still appearing available.

This rule applies to the `jewish_calendar` integration. Although it's an `iot_class: "calculated"` integration (meaning it primarily calculates data rather than fetching from an external I/O device), it relies on the `hdate` Python library for its core calculations. If the `hdate` library encounters an unrecoverable error and raises an exception during an entity's data computation, this can be considered equivalent to a "service" (the calculation service provided by `hdate`) being unavailable.

The integration currently does **NOT** fully follow this rule.
Specifically:

1.  **Sensor Entities (`sensor.py`):**
    *   The `JewishCalendarBaseSensor.async_update_data()` method performs calculations using `hdate.HDateInfo` and `self.make_zmanim()` (which internally uses `hdate.Zmanim`). This method is called once when the entity is added to Home Assistant via `async_added_to_hass()`.
    *   If these `hdate` calls raise an exception (e.g., due to a bug in the library or unexpected input not caught by validation), the `async_update_data()` method will propagate this exception.
    *   Critically, there is no `try...except` block around these calculations that sets `self._attr_available = False`.
    *   As a result, if an error occurs, `self.data.results` might not be populated or be stale, the entity's state might become `unknown` (as `native_value` properties return `None`), but the entity itself would remain `available = True` (the default).

    Relevant code snippet from `sensor.py` (`JewishCalendarBaseSensor.async_update_data`):
    ```python
    # ...
    # No try-except block here to handle exceptions from HDateInfo or make_zmanim
    # and set self._attr_available = False.
    daytime_date = HDateInfo(today, diaspora=self.data.diaspora)
    # ...
    today_times = self.make_zmanim(today)
    # ...
    self.data.results = JewishCalendarDataResults(
        daytime_date, after_shkia_date, after_tzais_date, today_times
    )
    # _attr_available is not explicitly managed based on calculation success/failure.
    ```

2.  **Binary Sensor Entities (`binary_sensor.py`):**
    *   The `JewishCalendarBinarySensor.is_on` property calculates the sensor's state on demand. This involves calls to `self.make_zmanim()` and subsequent access to the `zmanim` object's attributes/methods, all of which depend on the `hdate` library.
    *   The `_update()` callback method is responsible for triggering `self.async_write_ha_state()` which, in turn, reads the `is_on` property.
    *   If any `hdate`-related call within `make_zmanim()` or the `is_on` lambda (from `entity_description.is_on`) raises an exception, the `is_on` property will raise that exception.
    *   Home Assistant will likely catch this, log an error, and set the binary sensor's state to `unknown`. However, `_attr_available` is not set to `False` in this scenario. The entity would remain `available = True`.

    Relevant code snippet from `binary_sensor.py`:
    ```python
    # JewishCalendarBinarySensor.is_on property
    @property
    def is_on(self) -> bool:
        # No try-except to handle potential exceptions from make_zmanim()
        # or self.entity_description.is_on() that would then set _attr_available = False.
        zmanim = self.make_zmanim(dt.date.today())
        return self.entity_description.is_on(zmanim, dt_util.now())

    # JewishCalendarBinarySensor._update method
    @callback
    def _update(self, now: dt.datetime | None = None) -> None:
        # This method calls self.async_write_ha_state(), which reads .is_on
        # It does not currently manage availability based on calculation success/failure.
        self._update_unsub = None
        self._schedule_update()
        self.async_write_ha_state()
    ```

The case where `get_astral_event_date` returns `None` (e.g., in polar regions where sunset might not occur) is handled by sensor entities returning `None` for their state (leading to an "unknown" state). This specific scenario can be seen as "successfully fetching data" which indicates some "pieces of data are missing", and thus an "unknown" state for affected values is appropriate while the entity remains available. The primary gap for this rule relates to unhandled exceptions from the `hdate` library itself during its calculations.

## Suggestions

To make the `jewish_calendar` integration compliant with the `entity-unavailable` rule, the following changes are recommended:

1.  **For Sensor Entities (`sensor.py` - `JewishCalendarBaseSensor`):**
    *   Modify the `async_update_data` method to wrap the `hdate` library calls in a `try...except` block.
    *   If an exception occurs during these calculations, log the error and set `self._attr_available = False`.
    *   If calculations are successful, ensure `self._attr_available = True`.
    *   Ensure `self.data.results` is set to `None` or handled appropriately when an error occurs, so `native_value` properties behave consistently.

    ```python
    # homeassistant/components/jewish_calendar/sensor.py
    # Inside JewishCalendarBaseSensor class:

    # Initialize _attr_available to True (or rely on Entity class default)
    # _attr_available = True

    async def async_update_data(self) -> None:
        """Update the state of the sensor."""
        try:
            now = dt_util.now()
            _LOGGER.debug("Now: %s Location: %r", now, self.data.location)

            today = now.date()
            # Note: Handling of event_date is None is subtle. If it means
            # some data is missing but calculations can proceed partially,
            # entity might remain available with unknown states for some sensors.
            # The primary concern here is exceptions from hdate library.
            event_date = get_astral_event_date(self.hass, SUN_EVENT_SUNSET, today)

            if event_date is None:
                _LOGGER.warning(
                    "Sunset event date not available for %s. "
                    "Some zmanim-dependent sensor values may be unknown.",
                    today,
                )
                # Calculations will proceed, and hdate/sensors should handle None times appropriately.
                # Entity can remain available if hdate calls succeed.

            # Perform hdate calculations
            daytime_date = HDateInfo(today, diaspora=self.data.diaspora)
            
            # Initialize dependent dates
            after_shkia_date = daytime_date 
            after_tzais_date = daytime_date
            
            today_times = self.make_zmanim(today) # This call can raise exceptions

            if event_date: # Calculations dependent on sunset
                sunset = dt_util.as_local(event_date)
                _LOGGER.debug("Now: %s Sunset: %s", now, sunset)
                if now > sunset:
                    after_shkia_date = daytime_date.next_day
            
            # today_times.havdalah can be None if not applicable or not calculated
            if today_times.havdalah and now > today_times.havdalah:
                after_tzais_date = daytime_date.next_day
            
            self.data.results = JewishCalendarDataResults(
                daytime_date, after_shkia_date, after_tzais_date, today_times
            )
            self._attr_available = True  # Mark as available if all calculations succeed

        except Exception as ex:  # Catch potential exceptions from hdate or other calculations
            _LOGGER.error("Failed to calculate Jewish Calendar sensor data: %s", ex)
            self._attr_available = False
            self.data.results = None # Ensure results is cleared on failure
        # No self.async_write_ha_state() as this isn't the polled async_update.
        # State is read via properties after async_added_to_hass calls this.
    ```

2.  **For Binary Sensor Entities (`binary_sensor.py` - `JewishCalendarBinarySensor`):**
    *   Refactor the `_update` callback method. This method should be responsible for:
        *   Performing the `hdate` calculations to determine the sensor's state.
        *   Wrapping these calculations in a `try...except` block.
        *   Setting `self._attr_is_on` and `self._attr_available` based on the outcome.
        *   Scheduling the next update (this logic is currently in `_schedule_update`).
    *   The `is_on` property should then simply return the stored `self._attr_is_on` value.

    ```python
    # homeassistant/components/jewish_calendar/binary_sensor.py
    # Inside JewishCalendarBinarySensor class:

    # In __init__ or as class attributes:
    # self._attr_is_on: bool | None = None (already default for BinarySensorEntity)
    # self._attr_available: bool = True (already default for Entity)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        # Perform initial update, which now also sets availability and schedules next.
        # Call without arguments, _update will use dt_util.now().
        self._update() 

    @callback
    def _update(self, now_datetime: dt.datetime | None = None) -> None: # Parameter can be supplied by timer
        """Update the state of the sensor and schedule the next update."""
        # Clear any existing timer if this call is from a scheduled event
        if self._update_unsub:
            self._update_unsub() # Correctly call the stored unsubcriber
            self._update_unsub = None

        current_time = dt_util.now() # Use a consistent "now" for this update cycle
        next_update_point: dt.datetime | None = None

        try:
            zmanim = self.make_zmanim(current_time.date()) # Potential hdate exception
            new_state = self.entity_description.is_on(zmanim, current_time) # Lambda might raise

            if not self._attr_available: # If previously unavailable, log recovery
                _LOGGER.info(
                    "Jewish Calendar binary sensor %s (%s) is now available",
                    self.entity_id, self.entity_description.key
                )
            self._attr_available = True
            self._attr_is_on = new_state
            
            # Calculate next update point based on successful zmanim calculation
            # (Adapted from original _schedule_update logic)
            # Ensure zmanim times are timezone-aware (should be .local from hdate)
            
            # Default to next day's sunrise if no other specific events
            # Ensure zmanim.netz_hachama and its .local attribute are checked for None
            if zmanim.netz_hachama and zmanim.netz_hachama.local:
                next_update_point = zmanim.netz_hachama.local + dt.timedelta(days=1)
            else: # Fallback if netz_hachama is not available
                _LOGGER.warning("Netz Hachama not available for %s, scheduling generic next day update.", self.entity_id)
                next_update_point = (current_time + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


            candle_lighting = zmanim.candle_lighting
            if candle_lighting and candle_lighting.local and current_time < candle_lighting.local:
                if next_update_point is None or candle_lighting.local < next_update_point:
                    next_update_point = candle_lighting.local
            
            havdalah = zmanim.havdalah
            if havdalah and havdalah.local and current_time < havdalah.local:
                if next_update_point is None or havdalah.local < next_update_point:
                    next_update_point = havdalah.local
            
            if next_update_point is None: # Should ideally not happen if netz_hachama fallback exists
                 _LOGGER.error("Could not determine next update time for %s. Retrying in 1 hour.", self.entity_id)
                 next_update_point = current_time + dt.timedelta(hours=1)


        except Exception as e:
            if self._attr_available: # Log only if changing to unavailable
                _LOGGER.error(
                    "Error updating Jewish Calendar binary sensor %s (%s): %s. Marking unavailable.",
                    self.entity_id, self.entity_description.key, e
                )
            self._attr_available = False
            self._attr_is_on = None # Set state to None (unknown) when unavailable

            # Schedule a retry on failure
            next_update_point = current_time + dt.timedelta(minutes=5) # Retry in 5 minutes
            _LOGGER.info("Scheduling retry for %s (%s) in 5 minutes", self.entity_id, self.entity_description.key)

        # Schedule the next update
        if self.hass and next_update_point: # Ensure hass is set and we have a time
            self._update_unsub = event.async_track_point_in_time(
                self.hass, self._update, next_update_point
            )
        
        # Write HA state
        if self.hass: # Ensure Home Assistant is available
            self.async_write_ha_state()

    # The is_on property now simply returns the cached state
    @property
    def is_on(self) -> bool | None:
        """Return true if sensor is on."""
        return self._attr_is_on

    # The _schedule_update method is no longer needed as its logic is merged into _update.
    # def _schedule_update(self) -> None: ... (REMOVE)
    ```

These changes will ensure that if the `hdate` library (the core "service" for this integration) fails, the entities correctly reflect this by becoming unavailable, aligning with the `entity-unavailable` rule.

_Created at 2025-05-29 08:17:11. Prompt tokens: 13709, Output tokens: 3613, Total tokens: 29974_
