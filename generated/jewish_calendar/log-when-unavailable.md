# jewish_calendar: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `log-when-unavailable` rule requires that integrations log a message at `INFO` level when a connected device or service becomes unavailable, and again when it becomes available. This logging should only occur once per transition to avoid spamming logs.

This rule **applies** to the `jewish_calendar` integration. Although `jewish_calendar` is an `iot_class: calculated` integration (meaning it doesn't connect to external network devices or cloud services), it relies on internal calculations and Home Assistant helper functions that can fail:
1.  Calculations involving the `hdate` library (e.g., creating `HDateInfo`, `Zmanim` objects).
2.  Fetching solar data using `homeassistant.helpers.sun.get_astral_event_date`.

If these critical calculations fail, the entities provided by the integration cannot determine their correct state. According to the related `entity-unavailable` rule, entities should be marked as unavailable in such scenarios. Consequently, the `log-when-unavailable` rule applies to govern how these unavailability periods are logged.

The `jewish_calendar` integration currently does **not fully follow** this rule:

1.  **Handling of `get_astral_event_date` failure:**
    *   In `sensor.py`, within `JewishCalendarBaseSensor.async_update_data`, if `get_astral_event_date` returns `None`, an error is logged: `_LOGGER.error("Can't get sunset event date for %s", today)`.
    *   This logs at `ERROR` level, not `INFO` as required by the rule for unavailability notifications.
    *   The entity is not explicitly marked as unavailable (`self._attr_available = False`).
    *   There is no corresponding log message when `get_astral_event_date` starts succeeding again ("back online" message).

2.  **Handling of `hdate` library exceptions:**
    *   Calls to the `hdate` library (e.g., `HDateInfo(...)`, `self.make_zmanim(...)` which calls `Zmanim(...)`) in `sensor.py`'s `async_update_data` are not wrapped in a `try...except` block. If these calls raise an exception, it will be unhandled by the integration's code.
    *   While Home Assistant core might log an error for unhandled exceptions during entity updates, the integration itself does not manage the entity's availability state or provide the specific `INFO` level logs required by this rule.
    *   Similarly, `binary_sensor.py` calls `make_zmanim` in its `is_on` property and `_update` method without explicit error handling that would lead to unavailability logging as per this rule.

3.  **Lack of "log once" mechanism:**
    *   There is no mechanism (e.g., an instance variable like `_unavailable_logged`) to ensure that the unavailability log message is only emitted once when the state transitions to unavailable, and similarly for when it transitions back to available.

4.  **Entities not marked unavailable:**
    *   In the described failure scenarios, the integration does not explicitly set its entities to `unavailable`. For the rule to be fully effective, entities should first be correctly marked as unavailable when they cannot fetch or calculate their state.

## Suggestions

To make the `jewish_calendar` integration compliant with the `log-when-unavailable` rule, the following changes are recommended, primarily focusing on the `JewishCalendarBaseSensor` in `sensor.py` as it's responsible for fetching the core data (`self.data.results`) used by sensor entities.

1.  **Implement Robust Error Handling in `async_update_data`:**
    Wrap the critical calculations in `JewishCalendarBaseSensor.async_update_data` within a `try...except` block. This includes the call to `get_astral_event_date` and calls to the `hdate` library. Potentially long-running/CPU-intensive `hdate` calls should also be run in the executor using `hass.async_add_executor_job`.

2.  **Manage Entity Availability:**
    *   Add an instance variable `self._unavailable_logged: bool = False` to `JewishCalendarBaseSensor`.
    *   If calculations fail (e.g., `get_astral_event_date` returns `None` or `hdate` raises an exception):
        *   If `self.available` is `True` (i.e., it was previously available):
            *   Log an `INFO` message: `_LOGGER.info("Jewish Calendar sensor %s is unavailable: %s", self.entity_id, error_details_or_exception_str)`.
            *   Set `self._unavailable_logged = True`.
        *   Set `self._attr_available = False`.
    *   If calculations succeed:
        *   If `not self.available` (i.e., it was previously unavailable):
            *   Log an `INFO` message: `_LOGGER.info("Jewish Calendar sensor %s is back online.", self.entity_id)`.
            *   Set `self._unavailable_logged = False`.
        *   Set `self._attr_available = True`.
        *   Update `self.data.results` with the new data.

**Example for `JewishCalendarBaseSensor.async_update_data` in `sensor.py`:**

```python
# Add to JewishCalendarBaseSensor class definition:
# _unavailable_logged: bool = False # As a class attribute default
# Or initialize in __init__: self._unavailable_logged = False

async def async_update_data(self) -> None:
    """Update the state of the sensor."""
    try:
        now = dt_util.now()
        # _LOGGER.debug("Now: %s Location: %r", now, self.data.location) # Keep debug logs if useful
        today = now.date()

        # It's good practice to run potentially blocking calls in the executor
        event_date = await self.hass.async_add_executor_job(
            get_astral_event_date, self.hass, SUN_EVENT_SUNSET, today
        )

        if event_date is None:
            # Raise a specific exception to be caught by the common handler below
            raise RuntimeError(f"Cannot get sun event data for {today}")

        sunset = dt_util.as_local(event_date)
        # _LOGGER.debug("Now: %s Sunset: %s", now, sunset)

        # Wrap hdate library calls, ensure they are run in executor if blocking
        daytime_date = await self.hass.async_add_executor_job(
            HDateInfo, today, diaspora=self.data.diaspora
        )
        # make_zmanim itself calls hdate.Zmanim, so it should be run in executor
        # if Zmanim() is blocking.
        today_times = await self.hass.async_add_executor_job(
            self.make_zmanim, today
        )

        # Perform other calculations necessary for JewishCalendarDataResults
        # These might also need to be in executor if they involve more hdate calls
        after_tzais_date_val = daytime_date
        after_shkia_date_val = daytime_date

        if now > sunset:
            # Assuming HDateInfo.next_day is a property or simple method
            after_shkia_date_obj = await self.hass.async_add_executor_job(
                getattr, daytime_date, "next_day"
            )
            after_shkia_date_val = after_shkia_date_obj


        if today_times.havdalah and now > today_times.havdalah:
            after_tzais_date_obj = await self.hass.async_add_executor_job(
                getattr, daytime_date, "next_day"
            )
            after_tzais_date_val = after_tzais_date_obj
        
        current_results = JewishCalendarDataResults(
            daytime_date,
            after_shkia_date_val,
            after_tzais_date_val,
            today_times,
        )

        # If all successful up to this point:
        if not self.available:  # Check if it was previously unavailable
            _LOGGER.info(
                "Jewish Calendar sensor %s is back online", self.entity_id
            )
            # Reset flag if you choose to use _unavailable_logged as strictly "has the unavailable msg been logged"
            # self._unavailable_logged = False 
        self._attr_available = True
        self.data.results = current_results

    except Exception as ex: # Catch specific exceptions from hdate if possible, else broad Exception
        if self.available:  # Log only if it was previously available
            _LOGGER.info(
                "Jewish Calendar sensor %s is unavailable due to calculation error: %s",
                self.entity_id,
                ex, # Convert ex to string if necessary, or provide context
            )
            # self._unavailable_logged = True # Set flag if using it strictly for one-time logging
        self._attr_available = False
        # Optionally, clear self.data.results or leave it stale
        # self.data.results = None
```

3.  **Consider Binary Sensors:**
    The `JewishCalendarBinarySensor` entities in `binary_sensor.py` also perform calculations using `make_zmanim`.
    *   Their `_update` method should similarly manage `_attr_available` based on the success/failure of necessary calculations (like a test call to `make_zmanim`).
    *   The `is_on` property should return an appropriate value (e.g., `False` or `None`) if the sensor is unavailable.
    *   They should also implement the logging pattern (log once on transition to unavailable, once on transition back to available). This might involve having their own `_unavailable_logged` instance flags.

By implementing these changes, the `jewish_calendar` integration will more gracefully handle internal calculation failures, correctly reflect these as entity unavailability, and provide users with clear log messages as intended by the `log-when-unavailable` rule.

_Created at 2025-05-29 08:19:54. Prompt tokens: 13758, Output tokens: 2437, Total tokens: 27024_
