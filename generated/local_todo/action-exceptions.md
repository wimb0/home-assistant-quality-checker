# local_todo: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `action-exceptions` rule applies to the `local_todo` integration because it provides services that perform actions, specifically for managing to-do list items (create, update, delete, move). These actions can encounter failures, and the rule mandates that such failures should result in specific Home Assistant exceptions being raised.

The integration currently does **not** fully follow this rule. Here's a breakdown:

1.  **Incorrect Exception Type for Invalid Input:**
    In `todo.py`, the `async_move_todo_item` method correctly checks if the provided `uid` or `previous_uid` exist in the list. However, if an item is not found, it raises a `HomeAssistantError`:
    ```python
    # homeassistant/components/local_todo/todo.py
    if uid not in item_idx:
        raise HomeAssistantError(
            f"Item '{uid}' not found in todo list {self.entity_id}"
        )
    if previous_uid and previous_uid not in item_idx:
        raise HomeAssistantError(
            f"Item '{previous_uid}' not found in todo list {self.entity_id}"
        )
    ```
    According to the rule, "When the problem is caused by incorrect usage (for example incorrect input or referencing something that does not exist) we should raise a `ServiceValidationError`." An unknown `uid` or `previous_uid` is incorrect input.

2.  **Missing Exception Handling for Library Operations:**
    The service methods `async_create_todo_item`, `async_update_todo_item`, and `async_delete_todo_items` in `todo.py` interact with the `ical` library (specifically `TodoStore`). These methods call `todo_store.add()`, `todo_store.edit()`, and `todo_store.delete()` respectively, usually via `hass.async_add_executor_job`.
    *   These library calls could fail (e.g., `edit` or `delete` with a non-existent UID, `add` or `edit` with malformed data not caught by `_convert_item`).
    *   The current code does not appear to catch exceptions (e.g., `KeyError` if a UID is not found, or other `ical` library-specific exceptions) from these operations and re-raise them as `ServiceValidationError` (for bad input like non-existent UID) or `HomeAssistantError` (for unexpected library errors).

    For example, in `async_delete_todo_items`:
    ```python
    # homeassistant/components/local_todo/todo.py
    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete an item from the To-do list."""
        store = self._new_todo_store()
        async with self._calendar_lock:
            for uid in uids:
                store.delete(uid) # This call is not in a try/except block
            await self.async_save()
        await self.async_update_ha_state(force_refresh=True)
    ```
    If `store.delete(uid)` (executed in an executor job) raises an exception like `KeyError` because the `uid` doesn't exist, it will propagate uncaught by specific HA error handling.

3.  **Missing Exception Handling for I/O Operations in `async_save`:**
    The `async_save` method in `todo.py` is responsible for persisting the calendar to disk. It calls `self._store.async_store(content)`.
    ```python
    # homeassistant/components/local_todo/todo.py
    async def async_save(self) -> None:
        """Persist the todo list to disk."""
        content = IcsCalendarStream.calendar_to_ics(self._calendar)
        await self._store.async_store(content) # This can raise OSError
    ```
    The `LocalTodoListStore.async_store` method (in `store.py`) eventually calls `self._path.write_text(ics_content)`, which can raise `OSError` (e.g., disk full, permission denied).
    If an `OSError` occurs here during a service action (e.g., after creating an item), it will propagate uncaught by `async_save` as an `OSError` instead of being converted to a `HomeAssistantError`, which is more appropriate for an internal error during a service action.

## Suggestions

To make the `local_todo` integration compliant with the `action-exceptions` rule, the following changes are recommended:

1.  **Use `ServiceValidationError` for Invalid UIDs in `async_move_todo_item`:**
    Modify `homeassistant/components/local_todo/todo.py` to raise `ServiceValidationError` when a `uid` or `previous_uid` is not found:
    ```python
    from homeassistant.exceptions import HomeAssistantError, ServiceValidationError # Add ServiceValidationError

    # ... inside LocalTodoListEntity class

    async def async_move_todo_item(
        self, uid: str, previous_uid: str | None = None
    ) -> None:
        """Re-order an item to the To-do list."""
        if uid == previous_uid:
            return
        async with self._calendar_lock:
            todos = self._calendar.todos
            item_idx: dict[str, int] = {itm.uid: idx for idx, itm in enumerate(todos)}
            if uid not in item_idx:
                raise ServiceValidationError(  # Changed from HomeAssistantError
                    f"Item '{uid}' not found in todo list {self.entity_id}"
                )
            if previous_uid and previous_uid not in item_idx:
                raise ServiceValidationError(  # Changed from HomeAssistantError
                    f"Item '{previous_uid}' not found in todo list {self.entity_id}"
                )
            # ... rest of the method
    ```
    **Reasoning:** This aligns with the rule's requirement to use `ServiceValidationError` for errors caused by incorrect service call input.

2.  **Handle Exceptions from `ical` Library Operations:**
    Wrap calls to `ical` library methods within `try...except` blocks in `async_create_todo_item`, `async_update_todo_item`, and `async_delete_todo_items`.

    *   **For `async_create_todo_item`:**
        ```python
        # homeassistant/components/local_todo/todo.py
        async def async_create_todo_item(self, item: TodoItem) -> None:
            """Add an item to the To-do list."""
            todo = _convert_item(item)
            async with self._calendar_lock:
                todo_store = self._new_todo_store()
                try:
                    await self.hass.async_add_executor_job(todo_store.add, todo)
                except ValueError as err: # Example: if ical lib raises ValueError for bad data
                    _LOGGER.warning("Failed to add todo item due to invalid data: %s", err)
                    raise ServiceValidationError(f"Invalid data for new todo item: {err}") from err
                except Exception as err: # Catch other unexpected errors from the library
                    _LOGGER.error("Error adding todo item via ical library: %s", err)
                    raise HomeAssistantError(f"Failed to create todo item: {err}") from err
                await self.async_save() # async_save also needs error handling (see point 3)
            await self.async_update_ha_state(force_refresh=True)
        ```

    *   **For `async_update_todo_item`:**
        ```python
        # homeassistant/components/local_todo/todo.py
        async def async_update_todo_item(self, item: TodoItem) -> None:
            """Update an item to the To-do list."""
            if not item.uid: # Ensure UID is present for an update
                raise ServiceValidationError("Todo item UID is required for update.")
            todo = _convert_item(item)
            async with self._calendar_lock:
                todo_store = self._new_todo_store()
                try:
                    await self.hass.async_add_executor_job(todo_store.edit, todo.uid, todo)
                except KeyError as err: # Assuming ical raises KeyError if UID not found
                    _LOGGER.warning("Failed to update todo item, UID '%s' not found: %s", todo.uid, err)
                    raise ServiceValidationError(f"Todo item with UID '{todo.uid}' not found.") from err
                except ValueError as err: # Example: if ical lib raises ValueError for bad data
                    _LOGGER.warning("Failed to update todo item '%s' due to invalid data: %s", todo.uid, err)
                    raise ServiceValidationError(f"Invalid data for todo item '{todo.uid}': {err}") from err
                except Exception as err: # Catch other unexpected errors
                    _LOGGER.error("Error updating todo item '%s' via ical library: %s", todo.uid, err)
                    raise HomeAssistantError(f"Failed to update todo item '{todo.uid}': {err}") from err
                await self.async_save()
            await self.async_update_ha_state(force_refresh=True)
        ```

    *   **For `async_delete_todo_items`:**
        ```python
        # homeassistant/components/local_todo/todo.py
        async def async_delete_todo_items(self, uids: list[str]) -> None:
            """Delete an item from the To-do list."""
            if not uids:
                return
            store = self._new_todo_store()
            async with self._calendar_lock:
                for uid in uids:
                    try:
                        # Assuming store.delete is synchronous and run in executor
                        await self.hass.async_add_executor_job(store.delete, uid)
                    except KeyError as err: # Assuming ical raises KeyError if UID not found
                        # Log and potentially collect errors, or raise immediately.
                        # For simplicity here, we raise on first error.
                        # Consider if you want to attempt deleting others or stop.
                        _LOGGER.warning("Failed to delete todo item, UID '%s' not found: %s", uid, err)
                        raise ServiceValidationError(f"Todo item with UID '{uid}' not found.") from err
                    except Exception as err:
                        _LOGGER.error("Error deleting todo item '%s' via ical library: %s", uid, err)
                        raise HomeAssistantError(f"Failed to delete todo item '{uid}': {err}") from err
                await self.async_save()
            await self.async_update_ha_state(force_refresh=True)
        ```
    **Reasoning:** This ensures that failures within the `ical` library are caught and translated into appropriate Home Assistant exceptions, providing better feedback to the user and more robust error handling. *Developers should identify the specific exceptions raised by the `ical` library for different error conditions (e.g., item not found, invalid data) and catch them specifically.*

3.  **Handle `OSError` in `async_save`:**
    Modify the `async_save` method in `homeassistant/components/local_todo/todo.py` to catch `OSError` and raise `HomeAssistantError`.
    ```python
    # homeassistant/components/local_todo/todo.py
    async def async_save(self) -> None:
        """Persist the todo list to disk."""
        content = IcsCalendarStream.calendar_to_ics(self._calendar)
        try:
            await self._store.async_store(content)
        except OSError as err:
            _LOGGER.error("Error saving todo list to disk at %s: %s", self._store._path, err) # Assuming _store has a _path attribute
            raise HomeAssistantError(f"Failed to save todo list: {err}") from err
    ```
    **Reasoning:** File I/O errors are internal system issues, not user input errors. Raising `HomeAssistantError` correctly categorizes this type of failure. This protects service calls that invoke `async_save` from unhandled `OSError` exceptions.

By implementing these suggestions, the `local_todo` integration will better adhere to the `action-exceptions` rule, leading to a more robust and user-friendly experience.

_Created at 2025-05-28 23:34:52. Prompt tokens: 5062, Output tokens: 2964, Total tokens: 11907_
