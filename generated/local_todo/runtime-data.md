# local_todo: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule requires integrations to use the `ConfigEntry.runtime_data` attribute to store data that is not persisted to configuration storage but is needed during the lifetime of the configuration entry. This promotes consistency and enables typed access to this runtime data.

The `local_todo` integration **applies** this rule and **fully follows** it.

1.  **Typed ConfigEntry:**
    In `__init__.py`, a custom typed `ConfigEntry` is defined:
    ```python
    # __init__.py
    type LocalTodoConfigEntry = ConfigEntry[LocalTodoListStore]
    ```
    This explicitly types `entry.runtime_data` to be an instance of `LocalTodoListStore`.

2.  **Storing Runtime Data:**
    During the `async_setup_entry` function in `__init__.py`, an instance of `LocalTodoListStore` is created and then assigned to `entry.runtime_data`:
    ```python
    # __init__.py
    async def async_setup_entry(hass: HomeAssistant, entry: LocalTodoConfigEntry) -> bool:
        """Set up Local To-do from a config entry."""
        # ...
        store = LocalTodoListStore(hass, path)
        # ...
        entry.runtime_data = store
        # ...
        return True
    ```
    The `LocalTodoListStore` is the primary piece of runtime state for this integration, managing access to the to-do list data.

3.  **Accessing Runtime Data:**
    In the platform setup within `todo.py`, the `LocalTodoListStore` is correctly retrieved from `config_entry.runtime_data`. The function signature also uses the custom typed `LocalTodoConfigEntry`:
    ```python
    # todo.py
    from . import LocalTodoConfigEntry # Imports the typed ConfigEntry

    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: LocalTodoConfigEntry, # Uses the typed ConfigEntry
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up the local_todo todo platform."""

        store = config_entry.runtime_data # Accesses the typed runtime_data
        # ...
    ```

This implementation aligns perfectly with the rule's example and intent, ensuring that the `LocalTodoListStore` instance is managed consistently and is accessible in a type-safe manner throughout the config entry's lifecycle.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:30:16. Prompt tokens: 5028, Output tokens: 663, Total tokens: 7140_
