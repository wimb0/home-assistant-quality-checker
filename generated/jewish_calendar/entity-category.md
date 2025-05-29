# jewish_calendar: entity-category

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [entity-category](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-category)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-category` rule requires that entities are assigned an appropriate `EntityCategory` if the default category (`None`, for primary entities) is inappropriate. The `jewish_calendar` integration creates sensor and binary sensor entities.

This rule applies to the `jewish_calendar` integration because it defines entities.

The integration currently assigns `EntityCategory.DIAGNOSTIC` to all its sensor and binary_sensor entities. This is done in the base classes:
*   `JewishCalendarBaseSensor` in `sensor.py`:
    ```python
    class JewishCalendarBaseSensor(JewishCalendarEntity, SensorEntity):
        """Base class for Jewish calendar sensors."""

        _attr_entity_category = EntityCategory.DIAGNOSTIC
    ```
*   `JewishCalendarBinarySensor` in `binary_sensor.py`:
    ```python
    class JewishCalendarBinarySensor(JewishCalendarEntity, BinarySensorEntity):
        """Representation of an Jewish Calendar binary sensor."""

        _attr_should_poll = False
        _attr_entity_category = EntityCategory.DIAGNOSTIC
        # ...
    ```

However, the entities provided by this integration (e.g., Hebrew date, weekly Torah portion, holiday information, various Zmanim/times, Issur Melacha status) represent primary, core information derived from the Jewish calendar. They are not "diagnostic" in the sense of providing information about the health, status, or performance of the integration itself, a device, or the Home Assistant instance.

According to the Home Assistant developer documentation, `EntityCategory.DIAGNOSTIC` is for "Entities that provide diagnostic information about the integration, a device, or the Home Assistant instance itself." The entities in `jewish_calendar` provide calendarial and religious timing data, which are the primary function of the integration.

The default entity category (`None`) is appropriate for entities that provide a primary state representation. For the `jewish_calendar` entities, this default category would be more suitable. By explicitly setting `EntityCategory.DIAGNOSTIC`, the integration miscategorizes its primary entities, potentially leading to them being hidden or de-prioritized in auto-generated dashboards where users would expect to see them.

Therefore, the integration does not currently follow the rule because it assigns an inappropriate entity category to its entities.

## Suggestions

To make the integration compliant with the `entity-category` rule, the assigned `EntityCategory.DIAGNOSTIC` should be removed from the base classes for sensors and binary sensors. This will allow them to use the default entity category (`None`), which is appropriate for entities representing primary state information.

1.  **Modify `homeassistant/components/jewish_calendar/sensor.py`:**
    Remove the line `_attr_entity_category = EntityCategory.DIAGNOSTIC` from the `JewishCalendarBaseSensor` class.

    *Before:*
    ```python
    class JewishCalendarBaseSensor(JewishCalendarEntity, SensorEntity):
        """Base class for Jewish calendar sensors."""

        _attr_entity_category = EntityCategory.DIAGNOSTIC

        async def async_added_to_hass(self) -> None:
            # ...
    ```

    *After:*
    ```python
    class JewishCalendarBaseSensor(JewishCalendarEntity, SensorEntity):
        """Base class for Jewish calendar sensors."""

        async def async_added_to_hass(self) -> None:
            # ...
    ```

2.  **Modify `homeassistant/components/jewish_calendar/binary_sensor.py`:**
    Remove the line `_attr_entity_category = EntityCategory.DIAGNOSTIC` from the `JewishCalendarBinarySensor` class.

    *Before:*
    ```python
    class JewishCalendarBinarySensor(JewishCalendarEntity, BinarySensorEntity):
        """Representation of an Jewish Calendar binary sensor."""

        _attr_should_poll = False
        _attr_entity_category = EntityCategory.DIAGNOSTIC
        _update_unsub: CALLBACK_TYPE | None = None

        entity_description: JewishCalendarBinarySensorEntityDescription
        # ...
    ```

    *After:*
    ```python
    class JewishCalendarBinarySensor(JewishCalendarEntity, BinarySensorEntity):
        """Representation of an Jewish Calendar binary sensor."""

        _attr_should_poll = False
        _update_unsub: CALLBACK_TYPE | None = None

        entity_description: JewishCalendarBinarySensorEntityDescription
        # ...
    ```

By making these changes, the sensor and binary sensor entities provided by the `jewish_calendar` integration will correctly be classified as primary entities, aligning with their actual function and improving their presentation in the Home Assistant UI.

_Created at 2025-05-29 08:23:52. Prompt tokens: 13176, Output tokens: 1140, Total tokens: 16328_
