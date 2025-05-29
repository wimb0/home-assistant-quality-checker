# jewish_calendar: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `entity-unique-id` rule requires that all entities provided by an integration have a unique ID. This allows Home Assistant to track entities across restarts and enables users to customize them (e.g., rename, change entity ID).

This rule applies to the `jewish_calendar` integration as it provides `sensor` and `binary_sensor` entities.

The integration correctly implements unique IDs for its entities. This is primarily handled in the base entity class `JewishCalendarEntity` located in `homeassistant/components/jewish_calendar/entity.py`.

In the `__init__` method of `JewishCalendarEntity`, the unique ID is set as follows:
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
        """Initialize a Jewish Calendar entity."""
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}" # <--- This line sets the unique ID
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, config_entry.entry_id)},
        )
        self.data = config_entry.runtime_data
        set_language(self.data.language)
```
This pattern, `f"{config_entry.entry_id}-{description.key}"`, ensures uniqueness:
*   `config_entry.entry_id` is unique for each configuration instance of the integration.
*   `description.key` is unique for each type of sensor or binary sensor defined within the integration (as seen in `sensor.py` with `INFO_SENSORS`, `TIME_SENSORS` and in `binary_sensor.py` with `BINARY_SENSORS`).

Both `sensor` entities (inheriting from `JewishCalendarBaseSensor`, which inherits from `JewishCalendarEntity`) and `binary_sensor` entities (inheriting from `JewishCalendarEntity`) utilize this mechanism, thereby ensuring all created entities have a properly formatted and unique ID.

Furthermore, the `async_migrate_entry` function in `homeassistant/components/jewish_calendar/__init__.py` demonstrates an understanding and handling of unique IDs by providing a mechanism to migrate older unique ID formats to a newer, consistent format, which also uses `config_entry.entry_id`.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:07:06. Prompt tokens: 13369, Output tokens: 722, Total tokens: 14873_
