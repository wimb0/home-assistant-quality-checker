# local_todo: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **done**                                                                 |

## Overview

The `has-entity-name` rule requires that entities set the `_attr_has_entity_name = True` attribute. This enables a consistent and context-aware naming scheme for entities in Home Assistant.

This rule applies to the `local_todo` integration because it creates `todo` entities through the `LocalTodoListEntity` class.

The `local_todo` integration **follows** this rule.

The `LocalTodoListEntity` class, defined in `homeassistant/components/local_todo/todo.py`, correctly sets this attribute:

```python
# homeassistant/components/local_todo/todo.py
class LocalTodoListEntity(TodoListEntity):
    """A To-do List representation of the Shopping List."""

    _attr_has_entity_name = True  # Rule requirement met
    # ... (other attributes)

    def __init__(
        self,
        store: LocalTodoListStore,
        calendar: Calendar,
        name: str,  # This 'name' is from CONF_TODO_LIST_NAME
        unique_id: str,
    ) -> None:
        """Initialize LocalTodoListEntity."""
        # ...
        self._attr_name = name.capitalize() # Sets the entity's base name
        self._attr_unique_id = unique_id
        # ...
```

**Explanation of `_attr_name` usage:**

The rule provides examples related to entities associated with a device:
*   If an entity is a sub-feature of a device, `_attr_name` should be the sub-feature's name (e.g., "Temperature").
*   If an entity is the main feature of a device, `_attr_name` should be `None`, and the entity will inherit the device's name.

The `LocalTodoListEntity` in `local_todo` does not create or associate with a Home Assistant device. It is a standalone entity. According to Home Assistant's entity naming guidelines:
*   If `has_entity_name` is `True` and the entity has no device, the entity name will be the entity's `name` property.
*   The `name` property, in this case, is derived from `_attr_name`.

`LocalTodoListEntity` sets `self._attr_name` to the capitalized version of the user-provided `CONF_TODO_LIST_NAME` (e.g., "Groceries", "Work Tasks"). Since `_attr_has_entity_name` is `True` and there's no device, the entity's friendly name will directly be this user-provided name (e.g., "Groceries"). This is the desired and user-friendly behavior for standalone entities that represent a distinct, user-named item.

The integration correctly adheres to the primary requirement of setting `_attr_has_entity_name = True`, and its handling of `_attr_name` is appropriate for its standalone entity nature.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:29:54. Prompt tokens: 5157, Output tokens: 765, Total tokens: 11082_
