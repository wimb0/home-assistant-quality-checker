# jewish_calendar: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `parallel-updates` rule requires integrations to specify the number of parallel updates allowed for their entities, typically by defining a `PARALLEL_UPDATES` constant at the platform level (e.g., in `sensor.py`, `binary_sensor.py`). This is important for integrations interacting with devices or services that might be sensitive to a high volume of concurrent requests. A value of `0` indicates no limit, which is suitable when updates are centralized (e.g., via a coordinator) or when there's no external service involved.

This rule applies to the `jewish_calendar` integration as it provides `sensor` and `binary_sensor` entities.

The integration correctly follows this rule:

1.  **`sensor.py`**:
    The file `homeassistant/components/jewish_calendar/sensor.py` defines:
    ```python
    PARALLEL_UPDATES = 0
    ```
    This is appropriate because the sensor entities in this integration derive their state from a shared `JewishCalendarData` object, which is populated centrally. The data is calculated locally using the `hdate` library and does not involve external API calls that would need rate limiting. This aligns with the guidance for using `PARALLEL_UPDATES = 0` when data updates are centralized or no external limiting is needed. The `JewishCalendarBaseSensor.async_update_data` method populates `self.data.results` which is then used by individual sensor entities.

2.  **`binary_sensor.py`**:
    Similarly, the file `homeassistant/components/jewish_calendar/binary_sensor.py` defines:
    ```python
    PARALLEL_UPDATES = 0
    ```
    The binary sensors also rely on local calculations based on the `hdate` library and current time, rather than external service calls. The `JewishCalendarBinarySensor` entities calculate their state based on `Zmanim` objects derived locally and schedule their own updates using `event.async_track_point_in_time`. Setting `PARALLEL_UPDATES = 0` is suitable here as well.

The integration is of `iot_class: "calculated"`, meaning its primary function is to compute data rather than communicate with external devices or services. Therefore, limiting parallel updates in the traditional sense (to avoid overwhelming an external endpoint) is not necessary. Setting `PARALLEL_UPDATES = 0` correctly reflects this.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:20:16. Prompt tokens: 13427, Output tokens: 655, Total tokens: 15385_
