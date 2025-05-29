# local_todo: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unavailable` rule requires that integrations mark their entities as unavailable if they cannot fetch data from a device or service, or if interactions with that device/service fail in a way that compromises the entity's state. For the `local_todo` integration, the "service" is the local filesystem where ICS calendar files are stored.

This rule applies to `local_todo` because its core functionality relies on reading from and writing to these local ICS files.
-   **Initial Load:** The integration handles failures during the initial loading of the ICS file at setup (`async_setup_entry` in `homeassistant/components/local_todo/__init__.py`). If `store.async_load()` encounters an `OSError`, it correctly raises `ConfigEntryNotReady`. This prevents the entity from being set up and appearing in Home Assistant, which is an appropriate way to handle critical data fetching failures at startup.

-   **Runtime Operations (Saving Data):** The `LocalTodoListEntity` (defined in `homeassistant/components/local_todo/todo.py`) performs file write operations via its `async_save()` method. This method is crucial as it's called by all operations that modify the to-do list: `async_create_todo_item`, `async_update_todo_item`, `async_delete_todo_items`, and `async_move_todo_item`.
    If `async_save()` fails (e.g., due to an `OSError` like "disk full" or a "permission denied" error), the integration currently does not mark the entity as unavailable. An `OSError` will propagate upwards from `async_save()`, likely causing the service call (e.g., adding a to-do item) to fail and Home Assistant will log this error. However, the `LocalTodoListEntity` itself will remain in an "available" state (`self._attr_available` will remain `True` by default). This means Home Assistant might reflect an in-memory state that could not be persisted, leading to data inconsistency or loss upon restart. This behavior does not align with the rule, which expects the entity to become unavailable to signal that its state is unreliable due to issues with its backing service.

    For example, within the `async_create_todo_item` method in `homeassistant/components/local_todo/todo.py`:
    ```python
    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        todo = _convert_item(item)
        async with self._calendar_lock:
            todo_store = self._new_todo_store()
            await self.hass.async_add_executor_job(todo_store.add, todo)
            await self.async_save() # If this raises OSError, entity doesn't become unavailable
        await self.async_update_ha_state(force_refresh=True)
    ```
    If `await self.async_save()` raises an `OSError`, the exception will propagate out of this method, but no mechanism sets `self._attr_available = False`.

Therefore, while setup-time failures are handled appropriately by preventing entity creation, runtime failures critical to data integrity (like failing to save data) do not result in the entity being marked unavailable.

## Suggestions

To comply with the `entity-unavailable` rule, the `LocalTodoListEntity` should update its availability status when file save operations fail and, importantly, recover its available status when these operations subsequently succeed. This error handling and availability management logic should be implemented in all methods that call `async_save()`:
-   `async_create_todo_item`
-   `async_update_todo_item`
-   `async_delete_todo_items`
-   `async_move_todo_item`

The general pattern for these methods should be:

1.  Attempt to perform the calendar modification in memory and then persist it to disk using `async_save()`.
2.  If `async_save()` (or other critical parts of the operation that would render the state unreliable) raises an `OSError`:
    *   Log a clear error message.
    *   Set `self._attr_available = False`.
    *   Call `self.async_write_ha_state()` to immediately inform Home Assistant about the change in availability.
    *   Re-raise the original error or a new `HomeAssistantError` wrapping the original. This ensures that the service call that triggered the operation reports a failure to the user/frontend.
3.  If the entire operation, including `async_save()`, is successful:
    *   Ensure `self._attr_available = True`. This is particularly important if the entity was previously marked unavailable due to a prior error, allowing it to recover.
    *   Call `await self.async_update_ha_state(force_refresh=True)` (as is currently done for state updates) or `self.async_write_ha_state()` if only availability needed updating. This will update the entity's state and availability in Home Assistant.

**Example modification for `async_create_todo_item`:**

```python
# In homeassistant/components/local_todo/todo.py - within the LocalTodoListEntity class

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        todo = _convert_item(item)
        try:
            async with self._calendar_lock:
                todo_store = self._new_todo_store()
                # This modifies self._calendar in memory
                await self.hass.async_add_executor_job(todo_store.add, todo)
                # This attempts to persist the modified self._calendar to disk
                await self.async_save()

            # If all operations were successful, ensure entity is marked available.
            # self._attr_available defaults to True (from Entity base class).
            # This explicit step handles recovery if it was previously set to False.
            if not self._attr_available:
                self._attr_available = True
            
            # This updates _attr_todo_items from self._calendar and writes the new state to HA.
            # If self._attr_available was changed, this also pushes that update.
            await self.async_update_ha_state(force_refresh=True)

        except OSError as err:
            _LOGGER.error(
                "Failed to save To-do list '%s' for entity %s during item creation: %s",
                self.name,  # Or another suitable identifier for the list
                self.entity_id,
                err,
            )
            self._attr_available = False
            self.async_write_ha_state() # Immediately update availability state in HA
            # Re-raise to notify the frontend/user that the service call failed
            raise HomeAssistantError(
                f"Failed to save To-do list '{self.name}': {err}"
            ) from err
        # Note: Depending on the nature of _convert_item or todo_store.add,
        # other specific exceptions might warrant similar handling if they
        # indicate an unrecoverable or inconsistent state. For the
        # 'entity-unavailable' rule, OSError from I/O (like in async_save)
        # is the primary concern.
```

Applying this pattern consistently across all data modification methods will ensure that the `local_todo` entity accurately reflects its ability to interact with its backing filesystem storage, thereby adhering to the `entity-unavailable` rule by becoming unavailable when persistence fails and recovering when it succeeds.

_Created at 2025-05-28 23:37:47. Prompt tokens: 5311, Output tokens: 1806, Total tokens: 15824_
