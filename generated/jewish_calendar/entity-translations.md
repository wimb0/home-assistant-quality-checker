# jewish_calendar: entity-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [entity-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-translations)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-translations` rule requires that entities have translated names to enhance usability for non-English speakers. This is achieved by setting `_attr_has_entity_name = True` on the entity, providing a `_attr_translation_key` (often via an `EntityDescription`), and including corresponding name translations in the `strings.json` file.

This rule applies to the `jewish_calendar` integration as it creates `sensor` and `binary_sensor` entities.

The integration fully follows this rule:

1.  **`_attr_has_entity_name = True`**:
    The base entity class `JewishCalendarEntity` in `homeassistant/components/jewish_calendar/entity.py` correctly sets this attribute:
    ```python
    # homeassistant/components/jewish_calendar/entity.py
    class JewishCalendarEntity(Entity):
        """An HA implementation for Jewish Calendar entity."""

        _attr_has_entity_name = True
        # ...
    ```

2.  **`translation_key` specified for entities**:
    All sensor and binary sensor entities are defined using `EntityDescription` subclasses. Each of these descriptions includes a `translation_key`.

    For example, in `homeassistant/components/jewish_calendar/sensor.py`:
    *   Sensor descriptions in `INFO_SENSORS`:
        ```python
        # homeassistant/components/jewish_calendar/sensor.py
        INFO_SENSORS: tuple[JewishCalendarSensorDescription, ...] = (
            JewishCalendarSensorDescription(
                key="date",
                translation_key="hebrew_date", # <-- translation_key is set
                value_fn=lambda results: str(results.after_shkia_date.hdate),
                # ...
            ),
            JewishCalendarSensorDescription(
                key="weekly_portion",
                translation_key="weekly_portion", # <-- translation_key is set
                device_class=SensorDeviceClass.ENUM,
                # ...
            ),
            # ... more sensors
        )
        ```
    *   Timestamp sensor descriptions in `TIME_SENSORS`:
        ```python
        # homeassistant/components/jewish_calendar/sensor.py
        TIME_SENSORS: tuple[JewishCalendarTimestampSensorDescription, ...] = (
            JewishCalendarTimestampSensorDescription(
                key="alot_hashachar",
                translation_key="alot_hashachar", # <-- translation_key is set
                entity_registry_enabled_default=False,
            ),
            # ... more sensors
        )
        ```

    Similarly, for binary sensors in `homeassistant/components/jewish_calendar/binary_sensor.py`:
    ```python
    # homeassistant/components/jewish_calendar/binary_sensor.py
    BINARY_SENSORS: tuple[JewishCalendarBinarySensorEntityDescription, ...] = (
        JewishCalendarBinarySensorEntityDescription(
            key="issur_melacha_in_effect",
            translation_key="issur_melacha_in_effect", # <-- translation_key is set
            is_on=lambda state, now: bool(state.issur_melacha_in_effect(now)),
        ),
        # ... more binary sensors
    )
    ```
    When an entity is initialized (e.g., `JewishCalendarSensor`), its `entity_description` is assigned. Home Assistant's base `Entity` class uses `entity_description.translation_key` to find the appropriate translation.

3.  **`strings.json` provides translations**:
    The `homeassistant/components/jewish_calendar/strings.json` file contains the necessary translations for these keys under the `entity.<platform>.<translation_key>.name` path.

    Example for the sensor with `translation_key="hebrew_date"`:
    ```json
    // homeassistant/components/jewish_calendar/strings.json
    {
        "entity": {
            "sensor": {
                "hebrew_date": {
                    "name": "Date" // <-- Translated name
                },
                // ...
            }
        }
    }
    ```
    Example for the binary sensor with `translation_key="issur_melacha_in_effect"`:
    ```json
    // homeassistant/components/jewish_calendar/strings.json
    {
        "entity": {
            "binary_sensor": {
                "issur_melacha_in_effect": {
                    "name": "Issur Melacha in effect" // <-- Translated name
                },
                // ...
            }
        }
    }
    ```
    This structure and implementation align perfectly with the rule's requirements. Even for entities with a `device_class` (e.g., `weekly_portion` sensor with `SensorDeviceClass.ENUM`, or time sensors with `SensorDeviceClass.TIMESTAMP`), the integration provides explicit `translation_key`s and names, ensuring clear and specific entity naming rather than relying on default device class names. This is a valid and often preferred approach.

Therefore, the `jewish_calendar` integration correctly implements entity translations.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:27:09. Prompt tokens: 13511, Output tokens: 1279, Total tokens: 17939_
