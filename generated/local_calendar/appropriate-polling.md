# local_calendar: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_calendar](https://www.home-assistant.io/integrations/local_calendar/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **done**                                                                 |

## Overview

The `appropriate-polling` rule requires that integrations utilizing polling set a polling interval that is suitable for the data being fetched, aiming to minimize unnecessary requests while keeping data reasonably fresh.

This rule applies to the `local_calendar` integration. The `LocalCalendarEntity` in `calendar.py` implements the `async_update` method. According to Home Assistant's entity model, if an entity implements `async_update` (or `update`) and does not explicitly set `_attr_should_poll` to `False`, its `should_poll` property defaults to `True`. This makes the entity a "polling entity," and its `async_update` method will be called periodically at the frequency defined by `SCAN_INTERVAL`.

The `local_calendar` integration defines:
```python
# homeassistant/components/local_calendar/calendar.py
SCAN_INTERVAL = timedelta(days=1)
```

The `async_update` method in `LocalCalendarEntity` is responsible for refreshing the `self._event` attribute, which holds the next upcoming calendar event:
```python
# homeassistant/components/local_calendar/calendar.py
    async def async_update(self) -> None:
        """Update entity state with the next upcoming event."""

        def next_event() -> CalendarEvent | None:
            now = dt_util.now()
            # self._calendar is the in-memory representation
            events = self._calendar.timeline_tz(now.tzinfo).active_after(now)
            if event := next(events, None):
                return _get_calendar_event(event)
            return None

        self._event = await self.hass.async_add_executor_job(next_event)
```
This update operation reads from `self._calendar`, which is an *in-memory* representation of the calendar data. The actual `.ics` file on disk is loaded into `self._calendar` during the integration's setup (`async_setup_entry`) and is only modified (both in memory and on disk via `self._store.async_store()`) when Home Assistant services like `async_create_event`, `async_delete_event`, or `async_update_event` are called. These service calls also trigger an immediate state refresh using `self.async_update_ha_state(force_refresh=True)`.

The comment preceding `SCAN_INTERVAL` is informative:
```python
# The calendar on disk is only changed when this entity is updated, so there
# is no need to poll for changes. The calendar enttiy base class will handle
# refreshing the entity state based on the start or end time of the event.
```
This correctly notes that the `.ics` file on disk isn't polled for external changes. The defined `SCAN_INTERVAL` is for the periodic execution of `async_update`, which operates on the in-memory data.

Given these points:
1.  The entity `LocalCalendarEntity` is a polling entity due to its `async_update` implementation and default `should_poll=True`.
2.  The `SCAN_INTERVAL` is set to `timedelta(days=1)`.
3.  The `async_update` task is lightweight, involving a calculation on in-memory data that does not change unless explicitly modified by HA services (which also trigger immediate updates).
4.  The `CalendarEntity` base class also provides mechanisms for updating entity state based on event start/end times.

A polling interval of one day for re-calculating the next event from an in-memory, largely static (between HA-triggered modifications) data structure is highly appropriate. It is very infrequent and imposes minimal load, acting as a fallback or periodic refresh for the entity's `event` state.

Therefore, the `local_calendar` integration follows the `appropriate-polling` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:22:07. Prompt tokens: 6597, Output tokens: 953, Total tokens: 15611_
