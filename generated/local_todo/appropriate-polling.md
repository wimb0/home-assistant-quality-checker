# local_todo: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **exempt**                                       |
| Reason | The integration manages local data and does not actively poll for updates. State changes are event-driven, and the entity uses `_attr_should_poll = False`. |

## Overview

The `appropriate-polling` rule requires integrations that poll for data to set a sensible polling interval. This rule does **not apply** to the `local_todo` integration.

The `local_todo` integration is designed to manage to-do lists stored in local `.ics` files. Here's why it's exempt from the `appropriate-polling` rule:

1.  **No Active Polling for External Data:** The rule primarily targets integrations that poll external devices or services for data updates. The `local_todo` integration does not interact with any external entities; it manages files on the local filesystem.

2.  **Event-Driven Updates:** Data within the `local_todo` integration (the to-do items) changes in response to actions initiated within Home Assistant, such as a user adding, updating, or deleting a to-do item via the UI or a service call.
    *   Methods like `async_create_todo_item`, `async_update_todo_item`, and `async_delete_todo_items` in `homeassistant/components/local_todo/todo.py` handle these changes.
    *   After modifying the internal calendar data, these methods call `await self.async_save()` to persist changes to the `.ics` file and then `await self.async_update_ha_state(force_refresh=True)` to update the entity's state in Home Assistant. This is a reactive, not a polling, mechanism.

3.  **Entity-Level Polling Disabled:** The `LocalTodoListEntity` class in `homeassistant/components/local_todo/todo.py` explicitly disables polling by the Home Assistant core:
    ```python
    # homeassistant/components/local_todo/todo.py
    class LocalTodoListEntity(TodoListEntity):
        # ...
        _attr_should_poll = False
        # ...
    ```
    This means the `async_update` method of the entity is not called on a periodic schedule by Home Assistant.

4.  **No DataUpdateCoordinator for Polling:** The integration does not use a `DataUpdateCoordinator` with a defined `update_interval` for periodically fetching data. The data is loaded once during setup (`async_setup_entry` calls `store.async_load()`) and then managed in memory, updated only upon direct user interaction.

5.  **`iot_class: "local_polling"` Context:** While the `manifest.json` specifies `iot_class: "local_polling"`, this classification indicates that the integration interacts with local resources and *could* potentially poll them. However, the actual implementation details (as outlined above) show that it does not perform periodic polling for updates. The rule concerns the *actual act* of polling and its interval, which is not present here. The integration doesn't need to poll its own file for changes because it is the component making the changes to that file.

In summary, `local_todo` loads its data from a local file at startup and then modifies this data based on direct commands from Home Assistant. It does not periodically check an external source or its local file for unsolicited updates. Therefore, the concept of an "appropriate polling interval" as defined by the rule is not applicable.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:26:42. Prompt tokens: 5222, Output tokens: 848, Total tokens: 9447_
