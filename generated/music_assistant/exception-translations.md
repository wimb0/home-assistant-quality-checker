# music_assistant: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `strict-typing` rule applies to the `music_assistant` integration. This rule emphasizes the use of Python type hints to catch bugs early and improve code maintainability. A key requirement of this rule is: "If the integration implements `runtime-data`, the use of a custom typed `MyIntegrationConfigEntry` is required and must be used throughout."

The `music_assistant` integration defines a custom typed config entry:
```python
# homeassistant/components/music_assistant/__init__.py
type MusicAssistantConfigEntry = ConfigEntry[MusicAssistantEntryData]

@dataclass
class MusicAssistantEntryData:
    """Hold Mass data for the config entry."""
    mass: MusicAssistantClient
    listen_task: asyncio.Task
```
And it correctly uses `entry.runtime_data` to store instance-specific data:
```python
# homeassistant/components/music_assistant/__init__.py
    entry.runtime_data = MusicAssistantEntryData(mass, listen_task)
```

While the integration generally makes good use of type hints (e.g., `from __future__ import annotations` is present, function signatures and variables are often typed), it does not consistently use its custom `MusicAssistantConfigEntry` type "throughout" its codebase, specifically within `homeassistant/components/music_assistant/__init__.py`.

The following functions in `__init__.py` are defined to accept the generic `ConfigEntry` type instead of the more specific `MusicAssistantConfigEntry`, even though they operate on this integration's config entry and, in some cases, access or rely on its `runtime_data`:

1.  `async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:`
    *   This function directly accesses `entry.runtime_data`. For MyPy to correctly infer the type of `entry.runtime_data` as `MusicAssistantEntryData` at the point of access based on the function signature, `entry` should be typed as `MusicAssistantConfigEntry`.
    ```python
    # homeassistant/components/music_assistant/__init__.py
    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        # ...
        mass_entry_data: MusicAssistantEntryData = entry.runtime_data # Accesses runtime_data
        # ...
    ```

2.  `async def _client_listen(hass: HomeAssistant, entry: ConfigEntry, mass: MusicAssistantClient, init_ready: asyncio.Event) -> None:`
    *   This internal helper function is called with `entry` being an instance of `MusicAssistantConfigEntry`. While it doesn't directly access `entry.runtime_data`, it's an integral part of the config entry's lifecycle. Adhering to "used throughout" would mean typing `entry` as `MusicAssistantConfigEntry` for consistency and explicitness.
    ```python
    # homeassistant/components/music_assistant/__init__.py
    # Called as:
    # listen_task = asyncio.create_task(_client_listen(hass, entry, mass, init_ready))
    # where `entry` in async_setup_entry is MusicAssistantConfigEntry.
    async def _client_listen(
        hass: HomeAssistant,
        entry: ConfigEntry, # Should be MusicAssistantConfigEntry
        mass: MusicAssistantClient,
        init_ready: asyncio.Event,
    ) -> None:
        # ... uses entry.state, entry.entry_id
    ```

3.  `async def async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry) -> bool:`
    *   This function uses `config_entry.entry_id` to retrieve the `MusicAssistantClient` via `get_music_assistant_client`. The helper `get_music_assistant_client` itself correctly looks up and expects a `MusicAssistantConfigEntry` to access its `runtime_data.mass`. Typing `config_entry` here as `MusicAssistantConfigEntry` would make the chain of type expectations clearer and more robust.
    ```python
    # homeassistant/components/music_assistant/__init__.py
    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry # config_entry should be MusicAssistantConfigEntry
    ) -> bool:
        # ...
        mass = get_music_assistant_client(hass, config_entry.entry_id)
        # ...
    ```

Other files like `media_player.py` and `actions.py` correctly use `MusicAssistantConfigEntry` where appropriate (e.g., in their respective `async_setup_entry` or helper functions that retrieve the entry).

Due to these instances where the generic `ConfigEntry` is used instead of the specific `MusicAssistantConfigEntry` in `__init__.py`, the integration does not fully adhere to the `strict-typing` rule's requirement to use the custom typed `ConfigEntry` "throughout" when `runtime-data` is implemented.

## Suggestions

To make the `music_assistant` integration compliant with the `strict-typing` rule, the type hints for `ConfigEntry` parameters in the identified functions within `homeassistant/components/music_assistant/__init__.py` should be updated to use `MusicAssistantConfigEntry`.

1.  **Modify `async_unload_entry`:**
    Change the signature from:
    ```python
    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ```
    To:
    ```python
    async def async_unload_entry(hass: HomeAssistant, entry: MusicAssistantConfigEntry) -> bool:
    ```
    *Why:* This ensures that MyPy correctly understands `entry.runtime_data` is of type `MusicAssistantEntryData` without needing an explicit annotation at the point of assignment, making the code more type-safe and readable.

2.  **Modify `_client_listen`:**
    Change the signature from:
    ```python
    async def _client_listen(
        hass: HomeAssistant,
        entry: ConfigEntry,
        mass: MusicAssistantClient,
        init_ready: asyncio.Event,
    ) -> None:
    ```
    To:
    ```python
    async def _client_listen(
        hass: HomeAssistant,
        entry: MusicAssistantConfigEntry,
        mass: MusicAssistantClient,
        init_ready: asyncio.Event,
    ) -> None:
    ```
    *Why:* Although this function does not directly access `entry.runtime_data`, it is called with a `MusicAssistantConfigEntry` and is part of the entry-specific setup. Using the specific type aligns with the "used throughout" principle and improves clarity.

3.  **Modify `async_remove_config_entry_device`:**
    Change the signature from:
    ```python
    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
    ) -> bool:
    ```
    To:
    ```python
    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: MusicAssistantConfigEntry, device_entry: dr.DeviceEntry
    ) -> bool:
    ```
    *Why:* This function deals with a config entry specific to Music Assistant. Although `runtime_data` is accessed indirectly through a helper, using `MusicAssistantConfigEntry` makes the function's expectations about `config_entry` explicit and consistent.

By making these changes, the integration will better adhere to the strict typing requirements, particularly the mandate to use the custom typed `ConfigEntry` "throughout" the integration when `runtime_data` is utilized. This will improve type safety and maintainability, and prepare the integration for stricter MyPy checks if it's added to the `.strict-typing` file in Home Assistant core.

_Created at 2025-05-14 11:51:03. Prompt tokens: 29988, Output tokens: 1902, Total tokens: 36849_
