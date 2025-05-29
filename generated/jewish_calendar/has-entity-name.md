# jewish_calendar: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule requires entities to set `_attr_has_entity_name = True` to improve naming consistency across Home Assistant. When this attribute is true, an entity's name is typically formed by combining the device name with a specific name for the entity (e.g., "Device Name Sensor Name"). If the entity's specific name part is set to `None`, the entity will adopt the device name.

This rule applies to the `jewish_calendar` integration as it provides `sensor` and `binary_sensor` entities.

The integration correctly follows this rule:

1.  **Base Entity Class:** The `JewishCalendarEntity` class, defined in `homeassistant/components/jewish_calendar/entity.py`, serves as the base for all entities in this integration. It correctly sets `_attr_has_entity_name = True`:
    ```python
    # homeassistant/components/jewish_calendar/entity.py
    class JewishCalendarEntity(Entity):
        """An HA implementation for Jewish Calendar entity."""

        _attr_has_entity_name = True

        def __init__(
            self,
            config_entry: JewishCalendarConfigEntry,
            description: EntityDescription,
        ) -> None:
            # ...
            self._attr_device_info = DeviceInfo(
                entry_type=DeviceEntryType.SERVICE,
                identifiers={(DOMAIN, config_entry.entry_id)},
            )
            # ...
    ```

2.  **Entity Derivation:** All sensor entities (`JewishCalendarSensor`, `JewishCalendarTimeSensor` in `sensor.py`) and binary sensor entities (`JewishCalendarBinarySensor` in `binary_sensor.py`) inherit from `JewishCalendarEntity`. Therefore, they all inherit the `_attr_has_entity_name = True` attribute.

3.  **Entity Naming:**
    *   Entities are associated with a device. The device name is derived from the config entry's title, which defaults to "Jewish Calendar" (as set in `config_flow.py` using `DEFAULT_NAME` from `const.py`).
    *   Each entity uses an `EntityDescription` (e.g., `JewishCalendarSensorDescription`, `JewishCalendarTimestampSensorDescription`, `JewishCalendarBinarySensorEntityDescription`). These descriptions include a `translation_key` (e.g., `"hebrew_date"`, `"issur_melacha_in_effect"`).
    *   The `translation_key` is used in conjunction with `strings.json` to provide the specific name for the entity (e.g., "Date" for `hebrew_date`).
    *   With `_attr_has_entity_name = True`, Home Assistant will combine the device name and this specific entity name. For example, an entity with `translation_key="hebrew_date"` (translated to "Date") associated with the "Jewish Calendar" device will be named "Jewish Calendar Date". This behavior aligns with the rule's intention.

4.  **No Use of `_attr_name = None`:** The integration does not set `_attr_name = None` for any of its entities. This is appropriate as each entity represents a distinct piece of calendar information (e.g., a specific Zman, holiday status) and thus should have its own descriptive name appended to the device name, rather than just adopting the device name.

The implementation ensures that entity names are consistently formatted and clearly indicate their relationship to the "Jewish Calendar" device and their specific function.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:07:46. Prompt tokens: 13555, Output tokens: 901, Total tokens: 17472_
