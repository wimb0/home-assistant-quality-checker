# jewish_calendar: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **done**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `entity-event-setup` rule mandates that entities subscribing to events (e.g., from an integration library or Home Assistant's event helpers like timers) must do so within the `async_added_to_hass` method and perform cleanup (unsubscription) in the `async_will_remove_from_hass` method. This ensures that `self.hass` and `self.async_write_ha_state` are available when needed and prevents memory leaks.

This rule applies to the `jewish_calendar` integration because its binary sensor entities (`JewishCalendarBinarySensor`) subscribe to time-based events using `homeassistant.helpers.event.async_track_point_in_time` to manage their state updates.

The integration **fully follows** this rule for the entities that manage such subscriptions:

1.  **Subscription in `async_added_to_hass`:**
    In `homeassistant/components/jewish_calendar/binary_sensor.py`, the `JewishCalendarBinarySensor` class calls `self._schedule_update()` within its `async_added_to_hass` method:
    ```python
    # homeassistant/components/jewish_calendar/binary_sensor.py
    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self._schedule_update() # Initiates timer setup
    ```
    The `_schedule_update` method then uses `event.async_track_point_in_time` to register a callback (`self._update`). This occurs after `self.hass` is available.

2.  **Unsubscription in `async_will_remove_from_hass`:**
    The `JewishCalendarBinarySensor` class stores the unsubscribe callable returned by `event.async_track_point_in_time` in `self._update_unsub`. This callable is correctly invoked in `async_will_remove_from_hass` to cancel the timer:
    ```python
    # homeassistant/components/jewish_calendar/binary_sensor.py
    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        if self._update_unsub:
            self._update_unsub() # Cancels the timer
            self._update_unsub = None
        return await super().async_will_remove_from_hass()
    ```
    This ensures that resources are cleaned up when the entity is removed.

3.  **Safe access in callbacks:**
    The timer callback (`_update`) correctly calls `self.async_write_ha_state()`, which is safe because the timer is established after the entity is fully added to Home Assistant.

The `_schedule_update` method also demonstrates good practice by cancelling any existing timer before scheduling a new one:
```python
# homeassistant/components/jewish_calendar/binary_sensor.py
def _schedule_update(self) -> None:
    """Schedule the next update of the sensor."""
    # ... (calculates next update time 'update')
    if self._update_unsub: # Cancels previous timer if any
        self._update_unsub()
    self._update_unsub = event.async_track_point_in_time(
        self.hass, self._update, update
    )
```

The sensor entities defined in `homeassistant/components/jewish_calendar/sensor.py` (e.g., `JewishCalendarBaseSensor`, `JewishCalendarSensor`) currently do not subscribe to ongoing events or set up timers in `async_added_to_hass` that would necessitate explicit cleanup under this specific rule. They perform an initial data calculation in `async_added_to_hass` via `await self.async_update_data()`. As they do not manage such subscriptions, this rule's primary conditions for subscription/unsubscription management are not triggered for these sensor entities. If their update mechanism were to change to involve self-managed timers or event subscriptions, they would also need to adhere to this rule.

Given the correct implementation in `binary_sensor.py` where event subscriptions are actively managed, the integration complies with the `entity-event-setup` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:06:49. Prompt tokens: 13635, Output tokens: 1082, Total tokens: 21393_
