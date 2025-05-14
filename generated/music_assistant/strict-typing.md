# music_assistant: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `strict-typing` rule applies to the `music_assistant` integration. Python's dynamic typing can lead to bugs, and type hints, checked by mypy, help catch these early. For integrations using `entry.runtime_data`, a custom-typed `ConfigEntry` (e.g., `MyIntegrationConfigEntry = ConfigEntry[MyRuntimeData]`) is required and must be used throughout.

The `music_assistant` integration defines `type MusicAssistantConfigEntry = ConfigEntry[MusicAssistantEntryData]` in `homeassistant/components/music_assistant/__init__.py` and uses `entry.runtime_data`. However, it does not consistently use `MusicAssistantConfigEntry` throughout the codebase where a `ConfigEntry` object is handled, particularly when `runtime_data` is accessed.

**Key Violations and Areas for Improvement:**

1.  **Incorrect `ConfigEntry` type in `async_unload_entry`:**
    *   In `homeassistant/components/music_assistant/__init__.py`, the function `async_unload_entry` is defined as `async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:`.
    *   Inside this function, `entry.runtime_data` is accessed: `mass_entry_data: MusicAssistantEntryData = entry.runtime_data`.
    *   According to the rule, if `runtime_data` is accessed, the custom typed `MusicAssistantConfigEntry` must be used. The signature should be `async def async_unload_entry(hass: HomeAssistant, entry: MusicAssistantConfigEntry) -> bool:`. This is a direct violation.

2.  **Inconsistent `ConfigEntry` type usage:**
    *   In `homeassistant/components/music_assistant/__init__.py`, the functions `_client_listen` and `async_remove_config_entry_device` are defined with `entry: ConfigEntry`.
        *   `async def _client_listen(hass: HomeAssistant, entry: ConfigEntry, mass: MusicAssistantClient, init_ready: asyncio.Event) -> None:`
        *   `async def async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry) -> bool:` (here named `config_entry`)
    *   While these specific functions do not directly access `entry.runtime_data`, the rule states the custom typed `ConfigEntry` "must be used throughout." For strict compliance and consistency, these should also use `MusicAssistantConfigEntry`.

3.  **Missing `TypeVar` definitions in decorator:**
    *   In `homeassistant/components/music_assistant/media_player.py`, the `catch_musicassistant_error` decorator uses generic types `_R` and `P` (e.g., `func: Callable[Concatenate[MusicAssistantPlayer, P], Coroutine[Any, Any, _R]]`).
    *   These `TypeVar`s (`_R` and `P`) are not defined using `from typing import TypeVar`. This will cause Mypy errors.

4.  **Use of `Any` where more specific types might be possible:**
    *   In `homeassistant/components/music_assistant/media_browser.py`, the `build_item` function has `media_class: Any`. This could potentially be narrowed down to `MediaClass | str | None`.
    *   In `homeassistant/components/music_assistant/media_player.py`, `async_play_media` uses `**kwargs: Any`. If specific keys are expected from `ATTR_MEDIA_EXTRA`, a `TypedDict` could provide better typing.

5.  **Missing type hints for some local variables and module-level constants:**
    *   While Mypy can infer many local variable types, explicit annotations improve readability and strictness. Examples:
        *   `media_player.py`: `added_ids = set()` could be `set[str]`.
        *   `media_browser.py`: `PLAYABLE_MEDIA_TYPES` could be `list[str]`.

While the integration generally has good type coverage, including `from __future__ import annotations`, the issues above, especially the incorrect `ConfigEntry` typing in `async_unload_entry`, mean it does not fully follow the `strict-typing` rule.

## Suggestions

To make the `music_assistant` integration compliant with the `strict-typing` rule:

1.  **Correct `ConfigEntry` type in `__init__.py`:**
    *   Modify `async_unload_entry` to use `MusicAssistantConfigEntry`:
        ```python
        # In homeassistant/components/music_assistant/__init__.py
        async def async_unload_entry(
            hass: HomeAssistant, entry: MusicAssistantConfigEntry # Changed from ConfigEntry
        ) -> bool:
            unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

            if unload_ok:
                # No type error here now as entry is MusicAssistantConfigEntry
                mass_entry_data: MusicAssistantEntryData = entry.runtime_data
                mass_entry_data.listen_task.cancel()
                await mass_entry_data.mass.disconnect()

            return unload_ok
        ```
    *   For consistency and strict adherence to "must be used throughout," change `entry: ConfigEntry` to `entry: MusicAssistantConfigEntry` in the signatures of `_client_listen` and `async_remove_config_entry_device` as well:
        ```python
        # In homeassistant/components/music_assistant/__init__.py
        async def _client_listen(
            hass: HomeAssistant,
            entry: MusicAssistantConfigEntry, # Changed from ConfigEntry
            mass: MusicAssistantClient,
            init_ready: asyncio.Event,
        ) -> None:
            # ...
        
        async def async_remove_config_entry_device(
            hass: HomeAssistant, config_entry: MusicAssistantConfigEntry, device_entry: dr.DeviceEntry # Changed from ConfigEntry
        ) -> bool:
            # ...
        ```

2.  **Define `TypeVar`s in `media_player.py`:**
    *   At the top of `homeassistant/components/music_assistant/media_player.py` or just before the `catch_musicassistant_error` decorator, add:
        ```python
        from typing import TypeVar
        
        _MusicAssistantPlayerT = TypeVar("_MusicAssistantPlayerT", bound="MusicAssistantPlayer") # Assuming MusicAssistantPlayer is the self type
        _R = TypeVar("_R")
        # P is used with P.args and P.kwargs, suggesting it's a ParamSpec
        # from typing import ParamSpec (Python 3.10+)
        # P = ParamSpec("P")
        # If Python < 3.10, this part of the decorator typing might need rethinking or simplification
        # For now, let's assume Python 3.10+ for ParamSpec or acknowledge this as a complex spot.
        # Given Home Assistant's current Python version, ParamSpec is available.
        from typing import ParamSpec
        P = ParamSpec("P") 
        ```
    *   Then update the decorator signature:
        ```python
        def catch_musicassistant_error(
            func: Callable[Concatenate[_MusicAssistantPlayerT, P], Coroutine[Any, Any, _R]],
        ) -> Callable[Concatenate[_MusicAssistantPlayerT, P], Coroutine[Any, Any, _R]]:
            @functools.wraps(func)
            async def wrapper(
                self: _MusicAssistantPlayerT, *args: P.args, **kwargs: P.kwargs
            ) -> _R:
                # ...
        ```
        *Note: Ensure `_MusicAssistantPlayerT` correctly refers to the `MusicAssistantPlayer` class, possibly using a forward reference string if defined before the class.*

3.  **Refine `Any` types:**
    *   In `homeassistant/components/music_assistant/media_browser.py` for `build_item`:
        ```python
        from homeassistant.components.media_player import MediaClass # Ensure MediaClass is imported

        def build_item(
            mass: MusicAssistantClient,
            item: MediaItemType,
            can_expand: bool = True,
            media_class: MediaClass | str | None = None, # Changed from Any
        ) -> BrowseMedia:
            # ...
        ```
    *   For `**kwargs: Any` in `media_player.py::async_play_media`, if known keys from `ATTR_MEDIA_EXTRA` (like `use_pre_announce`, `announce_volume`, `radio_mode`) are processed, consider using `typing.TypedDict` for better clarity on expected extra parameters.

4.  **Add explicit type hints for variables and constants:**
    *   Example in `media_player.py`:
        ```python
        # In async_setup_entry
        added_ids: set[str] = set()
        mass_players: list[MusicAssistantPlayer] = []
        ```
    *   Example in `media_browser.py`:
        ```python
        from homeassistant.components.media_player import MediaType # If not already fully qualified

        PLAYABLE_MEDIA_TYPES: list[str | MediaType] = [ # Or just list[str] if they are all strings
            MediaType.ALBUM,
            # ... other types
        ]
        LIBRARY_TITLE_MAP: dict[str, str] = { ... }
        LIBRARY_MEDIA_CLASS_MAP: dict[str, MediaClass] = { ... }

        ```

By addressing these points, particularly the `MusicAssistantConfigEntry` usage and `TypeVar` definitions, the integration will better align with the `strict-typing` rule, leading to more robust and maintainable code.

_Created at 2025-05-14 11:59:12. Prompt tokens: 29988, Output tokens: 2356, Total tokens: 38795_
