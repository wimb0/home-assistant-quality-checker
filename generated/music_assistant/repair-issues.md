# music_assistant: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `strict-typing` rule applies to the `music_assistant` integration. This rule mandates the use of type hints throughout the codebase to enable static type checking with `mypy`, aiming to catch bugs early. For integrations implementing `runtime-data` (which `music_assistant` does via `entry.runtime_data`), a custom typed `ConfigEntry` (e.g., `MyIntegrationConfigEntry = ConfigEntry[MyData]`) is required and must be used consistently.

The `music_assistant` integration has made significant efforts towards adopting strict typing:
*   `from __future__ import annotations` is used in all Python files.
*   Many function signatures, variable annotations, and return types are hinted.
*   A custom typed config entry `MusicAssistantConfigEntry = ConfigEntry[MusicAssistantEntryData]` is defined in `homeassistant/components/music_assistant/__init__.py`.
*   The external library `music-assistant-client` and its models are used with type hints (e.g., `MusicAssistantClient`, `MassEvent`).

However, the integration does not fully follow the rule due to the following:

1.  **Inconsistent use of `MusicAssistantConfigEntry`**:
    The rule states: "If the integration implements `runtime-data`, the use of a custom typed `MyIntegrationConfigEntry` is required and must be used throughout."
    While `MusicAssistantConfigEntry` is defined and used in `async_setup_entry` and `media_player.async_setup_entry`, it's not used consistently in other functions within `homeassistant/components/music_assistant/__init__.py` that handle the config entry:
    *   `_client_listen(hass: HomeAssistant, entry: ConfigEntry, ...)` uses the generic `ConfigEntry`.
    *   `async_unload_entry(hass: HomeAssistant, entry: ConfigEntry)` uses the generic `ConfigEntry`. Consequently, `entry.runtime_data` needs a type assertion: `mass_entry_data: MusicAssistantEntryData = entry.runtime_data`. If `MusicAssistantConfigEntry` were used, `entry.runtime_data` would already be correctly typed.
    *   `async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, ...)` uses the generic `ConfigEntry`.

2.  **Use of `typing.Any`**:
    There are instances where `typing.Any` is used, which could potentially be more specific:
    *   In `homeassistant/components/music_assistant/media_browser.py`, the function `build_item` has `media_class: Any = None`. Based on its usage, this type could likely be narrowed down (e.g., to `MediaClass | str | None`).
    *   In `homeassistant/components/music_assistant/media_player.py`, the `async_play_media` method uses `**kwargs: Any`. While common for `**kwargs`, the values extracted from `kwargs[ATTR_MEDIA_EXTRA]` could potentially be typed more strictly if their structure is known (e.g., using a `TypedDict`).
    *   Functions in `schemas.py` returning `dict[str, Any]` (e.g., `media_item_dict_from_mass_item`) are common for data destined for schema validation or service responses. While acceptable, `TypedDict` could offer more precision.

3.  **Potential for Stricter MyPy Checks**:
    The rule mentions adding the integration to the `.strict-typing` file in Home Assistant core to enable stricter checks. For this to be effective, the codebase should aim for full type compliance.

Due to these points, particularly the inconsistent usage of the custom `ConfigEntry` type, the integration does not currently fully meet the `strict-typing` requirements.

## Suggestions

To make the `music_assistant` integration compliant with the `strict-typing` rule, consider the following:

1.  **Ensure Consistent Usage of `MusicAssistantConfigEntry`**:
    Modify the function signatures in `homeassistant/components/music_assistant/__init__.py` to use the specific `MusicAssistantConfigEntry` type instead of the generic `ConfigEntry` where applicable. This makes the expected type of `entry.runtime_data` explicit.

    *Example for `async_unload_entry`*:
    ```python
    # In homeassistant/components/music_assistant/__init__.py

    # Change this:
    # async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    #     """Unload a config entry."""
    #     unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    #     if unload_ok:
    #         mass_entry_data: MusicAssistantEntryData = entry.runtime_data # Type assertion needed
    #         mass_entry_data.listen_task.cancel()
    #         await mass_entry_data.mass.disconnect()
    #     return unload_ok

    # To this:
    async def async_unload_entry(hass: HomeAssistant, entry: MusicAssistantConfigEntry) -> bool:
        """Unload a config entry."""
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        if unload_ok:
            # entry.runtime_data is now correctly typed as MusicAssistantEntryData
            entry.runtime_data.listen_task.cancel()
            await entry.runtime_data.mass.disconnect()
        return unload_ok
    ```
    Apply similar changes to:
    *   `_client_listen(..., entry: MusicAssistantConfigEntry, ...)`
    *   `async_remove_config_entry_device(..., config_entry: MusicAssistantConfigEntry, ...)`

2.  **Refine `Any` Type Hints**:
    *   **`media_browser.build_item`**:
        The `media_class: Any` parameter in `build_item` (in `homeassistant/components/music_assistant/media_browser.py`) should be more specific. Looking at its usage, it's passed to `BrowseMedia` and seems to originate from `LIBRARY_MEDIA_CLASS_MAP` (values are `MediaClass`) or `_get_media_class_for_type` (returns `MediaClass | None`), or `item.media_type.value` (a `str`).
        *Suggested change*:
        ```python
        # In homeassistant/components/music_assistant/media_browser.py
        from homeassistant.components.media_player import MediaClass # Ensure MediaClass is imported

        def build_item(
            mass: MusicAssistantClient,
            item: MediaItemType,
            can_expand: bool = True,
            media_class: MediaClass | str | None = None, # Changed from Any
        ) -> BrowseMedia:
            # ...
        ```

3.  **Address `**kwargs: Any` in `media_player.async_play_media`**:
    If `kwargs[ATTR_MEDIA_EXTRA]` is expected to have a specific structure, define a `TypedDict` for it and type hint accordingly. This makes the expected keys and their types explicit.
    ```python
    # Example TypedDict (if applicable)
    # from typing import TypedDict, NotRequired
    #
    # class MediaExtraTyped(TypedDict):
    #     use_pre_announce: NotRequired[bool]
    #     announce_volume: NotRequired[int]
    #     radio_mode: NotRequired[bool]
    #
    # # In homeassistant/components/music_assistant/media_player.py
    # async def async_play_media(
    #     self,
    #     media_type: MediaType | str,
    #     media_id: str,
    #     enqueue: MediaPlayerEnqueue | None = None,
    #     announce: bool | None = None,
    #     **kwargs: Any, # Or more specific if ATTR_MEDIA_EXTRA is the only expected kwarg
    # ) -> None:
    #     media_extra: MediaExtraTyped | None = kwargs.get(ATTR_MEDIA_EXTRA)
    #     # ... use media_extra with type safety
    ```
    If `ATTR_MEDIA_EXTRA` is the only thing passed via `**kwargs`, consider making it an explicit parameter.

4.  **Run MyPy with Strict Flags**:
    After applying type improvements, run `mypy` with stricter flags (e.g., `--disallow-untyped-defs`, `--disallow-any-generics`) locally on the integration's codebase to catch any remaining typing issues.

5.  **Add to `.strict-typing` in Home Assistant Core**:
    Once the integration is fully typed and passes strict `mypy` checks, propose adding `homeassistant.components.music_assistant` to the `.strict-typing` file in the Home Assistant Core repository. This will enforce strict typing in CI.

By addressing these points, the `music_assistant` integration can achieve full compliance with the `strict-typing` rule, enhancing code quality and maintainability.

_Created at 2025-05-14 11:54:18. Prompt tokens: 29988, Output tokens: 2155, Total tokens: 36920_
