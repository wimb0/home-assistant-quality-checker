# music_assistant: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule requires integrations to use the `ConfigEntry.runtime_data` attribute to store data that is needed during the lifetime of the configuration entry but should not be persisted to storage. This approach promotes consistency and enables type safety for runtime data.

This rule applies to the `music_assistant` integration as it manages a `MusicAssistantClient` instance and an `asyncio.Task` for listening to events, both of which are typical examples of runtime data.

The `music_assistant` integration **fully follows** this rule.

1.  **Typed ConfigEntry and Data Structure**:
    In `homeassistant/components/music_assistant/__init__.py`, the integration defines a type alias for `ConfigEntry` specific to this integration and a dataclass for the runtime data:
    ```python
    type MusicAssistantConfigEntry = ConfigEntry[MusicAssistantEntryData]

    @dataclass
    class MusicAssistantEntryData:
        """Hold Mass data for the config entry."""

        mass: MusicAssistantClient
        listen_task: asyncio.Task
    ```
    This setup ensures that `entry.runtime_data` is expected to be of type `MusicAssistantEntryData`.

2.  **Usage in `async_setup_entry`**:
    The `async_setup_entry` function in `__init__.py` correctly uses the typed `MusicAssistantConfigEntry` and stores the runtime data:
    ```python
    async def async_setup_entry(
        hass: HomeAssistant, entry: MusicAssistantConfigEntry # Typed entry
    ) -> bool:
        # ...
        # store the listen task and mass client in the entry data
        entry.runtime_data = MusicAssistantEntryData(mass, listen_task) # Correct assignment
        # ...
    ```

3.  **Accessing `runtime_data`**:
    Runtime data is accessed correctly and with type awareness in other parts of the integration:
    *   In `__init__.py`'s `async_unload_entry`:
        ```python
        async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
            # ...
            if unload_ok:
                mass_entry_data: MusicAssistantEntryData = entry.runtime_data # Typed access
                mass_entry_data.listen_task.cancel()
                await mass_entry_data.mass.disconnect()
            # ...
        ```
        Even though `entry` is typed as generic `ConfigEntry` in the signature, `entry.runtime_data` is correctly accessed as `MusicAssistantEntryData`.
    *   In `homeassistant/components/music_assistant/actions.py` within `get_music_assistant_client`:
        ```python
        entry: MusicAssistantConfigEntry | None
        # ...
        return entry.runtime_data.mass
        ```
    *   In `homeassistant/components/music_assistant/media_player.py` within its `async_setup_entry`:
        ```python
        async def async_setup_entry(
            hass: HomeAssistant,
            entry: MusicAssistantConfigEntry, # Typed entry
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            mass = entry.runtime_data.mass # Typed access
            # ...
        ```

The integration consistently uses `entry.runtime_data` for its `MusicAssistantClient` and `listen_task`, and does so with appropriate typing, adhering to the rule's requirements and best practices.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:03:59. Prompt tokens: 30074, Output tokens: 900, Total tokens: 34549_
