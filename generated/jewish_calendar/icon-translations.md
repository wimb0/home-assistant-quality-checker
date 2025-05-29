# jewish_calendar: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `icon-translations` rule requires integrations to define entity icons in an `icons.json` file, referencing them via a `translation_key` in the entity definition, rather than hardcoding icons in Python code. This approach helps to centralize icon definitions and supports state-based or range-based icon changes.

This rule applies to the `jewish_calendar` integration as it defines custom icons for its sensor and binary sensor entities.

The `jewish_calendar` integration **fully follows** this rule.

1.  **Use of `translation_key`**:
    *   In `homeassistant/components/jewish_calendar/sensor.py`, sensor entities are defined using `JewishCalendarSensorDescription` and `JewishCalendarTimestampSensorDescription`. These descriptions consistently set the `translation_key` attribute. For example:
        ```python
        # sensor.py
        INFO_SENSORS: tuple[JewishCalendarSensorDescription, ...] = (
            JewishCalendarSensorDescription(
                key="date",
                translation_key="hebrew_date",
                # ...
            ),
            # ...
        )

        TIME_SENSORS: tuple[JewishCalendarTimestampSensorDescription, ...] = (
            JewishCalendarTimestampSensorDescription(
                key="alot_hashachar",
                translation_key="alot_hashachar",
                # ...
            ),
            # ...
        )
        ```
    *   Similarly, in `homeassistant/components/jewish_calendar/binary_sensor.py`, binary sensor entities use `JewishCalendarBinarySensorEntityDescription` which also sets `translation_key`:
        ```python
        # binary_sensor.py
        BINARY_SENSORS: tuple[JewishCalendarBinarySensorEntityDescription, ...] = (
            JewishCalendarBinarySensorEntityDescription(
                key="issur_melacha_in_effect",
                translation_key="issur_melacha_in_effect",
                # ...
            ),
            # ...
        )
        ```
    *   The base entity class `JewishCalendarEntity` (in `entity.py`) and its subclasses do not set `_attr_icon` directly, relying on the `translation_key` from their entity descriptions.

2.  **Presence and Correct Structure of `icons.json`**:
    *   The integration includes a `homeassistant/components/jewish_calendar/icons.json` file.
    *   This file correctly maps the `translation_key` values to MDI icons under the `entity.sensor` and `entity.binary_sensor` paths. For example:
        ```json
        // icons.json
        {
          "entity": {
            "binary_sensor": {
              "issur_melacha_in_effect": { "default": "mdi:power-plug-off" },
              // ...
            },
            "sensor": {
              "hebrew_date": { "default": "mdi:star-david" },
              "alot_hashachar": { "default": "mdi:weather-sunset-up" },
              // ...
            }
          }
        }
        ```
    *   The keys used in `icons.json` (e.g., `hebrew_date`, `alot_hashachar`, `issur_melacha_in_effect`) directly correspond to the `translation_key` values set in the Python entity descriptions.

3.  **No Hardcoded Icons in Python**:
    *   A review of the entity files (`entity.py`, `sensor.py`, `binary_sensor.py`) confirms that icons are not being set via `_attr_icon` in the entity classes or via the `icon` attribute in `EntityDescription`s.

4.  **Device Class Icons**:
    *   Some sensors, like those in `JewishCalendarTimeSensor`, use `_attr_device_class = SensorDeviceClass.TIMESTAMP`. The default icon for `TIMESTAMP` is `mdi:clock`. The `icons.json` file provides more specific icons for these (e.g., `mdi:weather-sunset` for `shkia`). This is an appropriate use of icon translations to provide more context-specific icons than the generic device class icon, and it adheres to the rule's intent.

The integration correctly uses the icon translation mechanism by defining `translation_key` for its entities and providing the corresponding icon definitions in `icons.json`. While it currently only uses "default" icons and not state-specific or range-based icons, this is not a violation, as the rule primarily concerns the method of defining icons, not the complexity of their state dependency.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:29:29. Prompt tokens: 14236, Output tokens: 1141, Total tokens: 18623_
