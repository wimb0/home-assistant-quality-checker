# local_todo: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |

## Overview

The `entity-unique-id` rule requires that all entities created by an integration have a unique ID. This is crucial for Home Assistant to track entities across restarts, allow user customizations (like renaming), and manage them in the entity registry.

This rule applies to the `local_todo` integration because it creates `TodoListEntity` instances, which are entities managed by Home Assistant.

The `local_todo` integration **fully follows** this rule. Each `LocalTodoListEntity` is assigned a unique ID derived from its corresponding config entry.

Specifically:
1.  In `homeassistant/components/local_todo/todo.py`, the `async_setup_entry` function instantiates `LocalTodoListEntity`:
    ```python
    # homeassistant/components/local_todo/todo.py
    entity = LocalTodoListEntity(store, calendar, name, unique_id=config_entry.entry_id)
    ```
    Here, `config_entry.entry_id` is passed as the `unique_id` argument. The `config_entry.entry_id` is guaranteed by Home Assistant to be unique for each configuration entry.

2.  The `LocalTodoListEntity` class constructor then assigns this passed `unique_id` to the `_attr_unique_id` attribute:
    ```python
    # homeassistant/components/local_todo/todo.py
    class LocalTodoListEntity(TodoListEntity):
        # ...
        def __init__(
            self,
            store: LocalTodoListStore,
            calendar: Calendar,
            name: str,
            unique_id: str,
        ) -> None:
            """Initialize LocalTodoListEntity."""
            # ...
            self._attr_unique_id = unique_id
    ```
    Setting `self._attr_unique_id` is the standard way to define an entity's unique ID.

Since each `LocalTodoListEntity` corresponds to a unique config entry, and `config_entry.entry_id` is used as the unique ID, each entity created by this integration will have a stable and unique identifier within its domain and platform, satisfying the rule's requirements.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:28:53. Prompt tokens: 4971, Output tokens: 589, Total tokens: 7856_
