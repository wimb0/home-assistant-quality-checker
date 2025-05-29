# local_todo: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The `LocalTodoListEntity` does not subscribe to external events that push updates to it. Its state changes are initiated by Home Assistant service calls, not by reacting to asynchronous events from a library or other sources. |

## Overview

The `entity-event-setup` rule mandates that entities subscribing to external events (e.g., from an integration's client library) must set up these subscriptions in the `async_added_to_hass` method and tear them down in `async_will_remove_from_hass`. This ensures that subscriptions are active only when the entity is fully initialized and part of Home Assistant, and that they are cleaned up properly to prevent memory leaks.

This rule does not apply to the `local_todo` integration. The `LocalTodoListEntity` in `todo.py` manages a local ICS file. Its state is updated through direct calls to its methods (e.g., `async_create_todo_item`, `async_update_todo_item`) which are typically triggered by Home Assistant service calls or user interactions.

Specifically:
*   The `LocalTodoListEntity` does not instantiate or use any client library that emits events it needs to subscribe to.
*   It interacts with the `ical` library for parsing and generating ICS content, but these interactions are synchronous calls within the entity's methods (e.g., `IcsCalendarStream.calendar_from_ics`, `todo_store.add`). The `ical` library, in this context of use, is not an event-emitting source that the entity subscribes to for push updates.
*   The entity's data (`self._calendar`) is modified directly by its own methods, and then `self.async_update_ha_state(force_refresh=True)` is called to signal Home Assistant to refresh its state.
*   The entity does not implement `async_added_to_hass` or `async_will_remove_from_hass` for the purpose of event subscription management, as there are no such events to manage.
*   While the integration is classified as `local_polling`, the `LocalTodoListEntity` itself has `_attr_should_poll = False`, indicating it does not rely on periodic polling for updates but rather updates reactively to service calls.

Because the `LocalTodoListEntity` does not subscribe to any external, asynchronous events that would trigger state updates, the requirements for managing such subscriptions in specific lifecycle methods (`async_added_to_hass`, `async_will_remove_from_hass`) are not applicable.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:28:24. Prompt tokens: 5237, Output tokens: 659, Total tokens: 7962_
