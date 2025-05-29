# jewish_calendar: entity-device-class

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [entity-device-class](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-device-class)                                                     |
| Status | **todo**                                                                 |

## Overview

The `entity-device-class` rule requires entities to use device classes where possible to provide context, which Home Assistant uses for UI representation, voice control, cloud integrations, and more. This rule applies to the `jewish_calendar` integration as it creates sensor and binary sensor entities (as defined by `PLATFORMS` in `__init__.py`).

The integration partially follows this rule:

**Sensor Entities (`sensor.py`):**
*   The integration correctly uses `SensorDeviceClass.ENUM` for the `weekly_portion` and `holiday` sensors. This is appropriate as these sensors have a state that comes from a predefined list of options.
    ```python
    # homeassistant/components/jewish_calendar/sensor.py
    INFO_SENSORS: tuple[JewishCalendarSensorDescription, ...] = (
        # ...
        JewishCalendarSensorDescription(
            key="weekly_portion",
            translation_key="weekly_portion",
            device_class=SensorDeviceClass.ENUM, # Correct usage
            options_fn=lambda _: [str(p) for p in Parasha],
            value_fn=lambda results: str(results.after_tzais_date.upcoming_shabbat.parasha),
        ),
        JewishCalendarSensorDescription(
            key="holiday",
            translation_key="holiday",
            device_class=SensorDeviceClass.ENUM, # Correct usage
            options_fn=lambda diaspora: HolidayDatabase(diaspora).get_all_names(),
            value_fn=lambda results: ", ".join(
                str(holiday) for holiday in results.after_shkia_date.holidays
            ),
            # ...
        ),
        # ...
    )
    ```
*   All time-related sensors defined in `TIME_SENSORS` correctly use `SensorDeviceClass.TIMESTAMP` through the `JewishCalendarTimeSensor` base class:
    ```python
    # homeassistant/components/jewish_calendar/sensor.py
    class JewishCalendarTimeSensor(JewishCalendarBaseSensor):
        """Implement attributes for sensors returning times."""

        _attr_device_class = SensorDeviceClass.TIMESTAMP # Correct usage
        entity_description: JewishCalendarTimestampSensorDescription
        # ...
    ```
*   Sensors like `date` (Hebrew date string), `omer_count` (numeric count), and `daf_yomi` (custom string) do not have a device class assigned. This is acceptable because there isn't a standard `SensorDeviceClass` that accurately describes their specific nature (e.g., a formatted Hebrew date string, a simple day count, or a Talmudic page reference). The rule specifies using device classes "where possible," and in these cases, a standard class would not fit well.

**Binary Sensor Entities (`binary_sensor.py`):**
*   The integration currently does **not** assign device classes to its binary sensors. The `JewishCalendarBinarySensorEntityDescription` dataclass does not include a `device_class` field, and none are assigned in the `BINARY_SENSORS` tuple definitions:
    ```python
    # homeassistant/components/jewish_calendar/binary_sensor.py
    @dataclass(frozen=True)
    class JewishCalendarBinarySensorEntityDescription(
        JewishCalendarBinarySensorMixIns, BinarySensorEntityDescription
    ):
        """Binary Sensor Entity description for Jewish Calendar."""
        # No device_class attribute defined here by default

    BINARY_SENSORS: tuple[JewishCalendarBinarySensorEntityDescription, ...] = (
        JewishCalendarBinarySensorEntityDescription(
            key="issur_melacha_in_effect",
            translation_key="issur_melacha_in_effect",
            is_on=lambda state, now: bool(state.issur_melacha_in_effect(now)),
            # No device_class assigned
        ),
        JewishCalendarBinarySensorEntityDescription(
            key="erev_shabbat_hag",
            translation_key="erev_shabbat_hag",
            is_on=lambda state, now: bool(state.erev_shabbat_chag(now)),
            entity_registry_enabled_default=False,
            # No device_class assigned
        ),
        JewishCalendarBinarySensorEntityDescription(
            key="motzei_shabbat_hag",
            translation_key="motzei_shabbat_hag",
            is_on=lambda state, now: bool(state.motzei_shabbat_chag(now)),
            entity_registry_enabled_default=False,
            # No device_class assigned
        ),
    )
    ```
    For these binary sensors, appropriate device classes could be assigned to provide better context to Home Assistant and improve integration with voice assistants and cloud services.

Because some binary sensor entities could benefit from a device class but do not currently use one, the integration is marked as "todo".

## Suggestions

To make the `jewish_calendar` integration fully compliant with the `entity-device-class` rule, assign appropriate `BinarySensorDeviceClass` values to the binary sensor entity descriptions in `homeassistant/components/jewish_calendar/binary_sensor.py`.

1.  **Import `BinarySensorDeviceClass`:**
    Add the import to `homeassistant/components/jewish_calendar/binary_sensor.py`:
    ```python
    from homeassistant.components.binary_sensor import (
        BinarySensorDeviceClass, # Add this line
        BinarySensorEntity,
        BinarySensorEntityDescription,
    )
    ```

2.  **Update `BINARY_SENSORS` definitions:**

    *   For the `issur_melacha_in_effect` sensor (Indicates if religious work restrictions are active):
        *   **Suggestion:** Use `device_class=BinarySensorDeviceClass.LOCK`.
        *   **Reasoning:** When this sensor is `ON` (restrictions are in effect), it signifies that certain activities are "locked" or prohibited. The `LOCK` device class semantically fits this concept of restriction and is well-understood by voice assistants and cloud platforms.
        ```python
        JewishCalendarBinarySensorEntityDescription(
            key="issur_melacha_in_effect",
            translation_key="issur_melacha_in_effect",
            device_class=BinarySensorDeviceClass.LOCK, # Suggested change
            is_on=lambda state, now: bool(state.issur_melacha_in_effect(now)),
        ),
        ```

    *   For the `erev_shabbat_hag` sensor (Indicates if it's currently the eve of Shabbat or a holiday) and `motzei_shabbat_hag` sensor (Indicates if it's currently the conclusion of Shabbat or a holiday):
        *   **Suggestion:** Use `device_class=BinarySensorDeviceClass.RUNNING`.
        *   **Reasoning:** These sensors indicate whether a specific calendar-defined period is currently active. When `ON`, the respective period (e.g., "Erev Shabbat") can be considered "running" or "in progress." This provides a general context of activity for these time-based states.
        ```python
        JewishCalendarBinarySensorEntityDescription(
            key="erev_shabbat_hag",
            translation_key="erev_shabbat_hag",
            device_class=BinarySensorDeviceClass.RUNNING, # Suggested change
            is_on=lambda state, now: bool(state.erev_shabbat_chag(now)),
            entity_registry_enabled_default=False,
        ),
        JewishCalendarBinarySensorEntityDescription(
            key="motzei_shabbat_hag",
            translation_key="motzei_shabbat_hag",
            device_class=BinarySensorDeviceClass.RUNNING, # Suggested change
            is_on=lambda state, now: bool(state.motzei_shabbat_chag(now)),
            entity_registry_enabled_default=False,
        ),
        ```

By implementing these changes, the binary sensors will provide more semantic context to Home Assistant, potentially improving their representation in the UI and their behavior with voice assistants and cloud integrations, thus satisfying the `entity-device-class` rule.

_Created at 2025-05-29 08:25:25. Prompt tokens: 13449, Output tokens: 1944, Total tokens: 21890_
