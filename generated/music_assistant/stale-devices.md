# music_assistant: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `strict-typing` rule applies to the `music_assistant` integration as it is a general requirement for all integrations aiming for higher quality by leveraging Python's type hinting capabilities for early bug detection.

The integration currently does **not** fully follow this rule. Here's a breakdown:

1.  **Custom Typed ConfigEntry Usage**:
    The rule states: "If the integration implements `runtime-data`, the use of a custom typed `MyIntegrationConfigEntry` is required and must be used throughout."
    The `music_assistant` integration defines `type MusicAssistantConfigEntry = ConfigEntry[MusicAssistantEntryData]` in `__init__.py` because it uses `entry.runtime_data`.
    However, this custom type is not used consistently:
    *   In `homeassistant/components/music_assistant/__init__.py`:
        *   `async def _client_listen(hass: HomeAssistant, entry: ConfigEntry, ...)` should use `entry: MusicAssistantConfigEntry`.
        *   `async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) ...` should use `entry: MusicAssistantConfigEntry`.
        *   `async def async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, ...)` should use `config_entry: MusicAssistantConfigEntry`.
    Failure to use the specific `MusicAssistantConfigEntry` type means that `entry.runtime_data` is treated as `Any` by mypy in those contexts, reducing type safety.

2.  **Use of `Any` Type**:
    Strict typing aims to replace `Any` with more specific types where possible.
    *   In `homeassistant/components/music_assistant/media_browser.py`:
        *   The function `build_item` has a parameter `media_class: Any = None`. Based on its usage, this could be typed more specifically, for example, as `MediaClass | str | None`.
    *   In `homeassistant/components/music_assistant/media_player.py`:
        *   The method `async_play_media(..., **kwargs: Any)` inherits `**kwargs: Any` from the base `MediaPlayerEntity`. While the signature might be fixed, the internal handling of `kwargs` (specifically `kwargs[ATTR_MEDIA_EXTRA]`) could be made more type-safe using `cast` or more robust access patterns to inform mypy about the expected structure. Currently, direct access like `kwargs[ATTR_MEDIA_EXTRA].get(...)` assumes `kwargs[ATTR_MEDIA_EXTRA]` exists and is a dictionary, which mypy (with `Any`) won't check.

3.  **Library Typing (PEP-561 Compliance)**:
    A core requirement of the `strict-typing` rule is: "we recommend fully typing your library and making your library PEP-561 compliant. This means that you need to add a `py.typed` file to your library."
    The `music_assistant` integration depends on `music-assistant-client==1.2.0`. For the `strict-typing` rule to be fully met, this external library must:
    *   Be fully type-hinted.
    *   Include a `py.typed` marker file in its package to declare itself as PEP-561 compliant.
    Without this, mypy running on Home Assistant core cannot effectively type-check interactions with the `music-assistant-client` library, limiting the benefits of strict typing for the integration. The compliance of this library needs to be verified by the developers.

4.  **`.strict-typing` File in Home Assistant Core**:
    The rule also mentions: "In the Home Assistant codebase, you can add your integration to the [`.strict-typing`](https://github.com/home-assistant/core/blob/dev/.strict-typing) file, which will enable strict type checks for your integration."
    It's not specified whether `music_assistant` is currently in this file. Adding it would enable more rigorous checks by mypy on the integration's own code.

Due to these points, particularly the inconsistent use of the typed `ConfigEntry`, the presence of `Any`, and the critical dependency on the external library's typing status, the integration is marked as "todo".

## Suggestions

To make the `music_assistant` integration compliant with the `strict-typing` rule, consider the following actionable steps:

1.  **Consistently Use `MusicAssistantConfigEntry`**:
    Modify function signatures in `homeassistant/components/music_assistant/__init__.py` to use the specific `MusicAssistantConfigEntry` type instead of the generic `ConfigEntry`:
    *   Change:
        ```python
        async def _client_listen(
            hass: HomeAssistant,
            entry: ConfigEntry, # <-- Change this
            mass: MusicAssistantClient,
            init_ready: asyncio.Event,
        ) -> None:
        ```
        To:
        ```python
        async def _client_listen(
            hass: HomeAssistant,
            entry: MusicAssistantConfigEntry, # <-- To this
            mass: MusicAssistantClient,
            init_ready: asyncio.Event,
        ) -> None:
        ```
    *   Change:
        ```python
        async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool: # <-- Change this
        ```
        To:
        ```python
        async def async_unload_entry(hass: HomeAssistant, entry: MusicAssistantConfigEntry) -> bool: # <-- To this
        ```
        This will ensure that `entry.runtime_data` is correctly typed as `MusicAssistantEntryData`.
    *   Change:
        ```python
        async def async_remove_config_entry_device(
            hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry # <-- Change this
        ) -> bool:
        ```
        To:
        ```python
        async def async_remove_config_entry_device(
            hass: HomeAssistant, config_entry: MusicAssistantConfigEntry, device_entry: dr.DeviceEntry # <-- To this
        ) -> bool:
        ```

2.  **Refine `Any` Type Usage**:
    *   In `homeassistant/components/music_assistant/media_browser.py`, for the `build_item` function:
        Change:
        ```python
        def build_item(
            mass: MusicAssistantClient,
            item: MediaItemType,
            can_expand: bool = True,
            media_class: Any = None, # <-- Change this
        ) -> BrowseMedia:
        ```
        To a more specific type based on usage, e.g.:
        ```python
        from homeassistant.components.media_player import MediaClass # Ensure import

        def build_item(
            mass: MusicAssistantClient,
            item: MediaItemType,
            can_expand: bool = True,
            media_class: MediaClass | str | None = None, # <-- To this
        ) -> BrowseMedia:
        ```
    *   For methods like `async_play_media(..., **kwargs: Any)` in `media_player.py` that override base class methods with `**kwargs: Any`:
        While the signature cannot change, improve internal type safety when accessing `kwargs`. For example, when dealing with `ATTR_MEDIA_EXTRA`:
        ```python
        # from typing import cast
        # ...
        # inside async_play_media
        media_extra_raw = kwargs.get(ATTR_MEDIA_EXTRA)
        media_extra: dict[str, Any] = {}
        if isinstance(media_extra_raw, dict):
            media_extra = media_extra_raw
        
        # Then use media_extra, e.g.:
        use_pre_announce = media_extra.get("use_pre_announce")
        announce_volume = media_extra.get("announce_volume")
        radio_mode = media_extra.get(ATTR_RADIO_MODE) 
        # ... when calling _async_handle_play_media
        # radio_mode=media_extra.get(ATTR_RADIO_MODE),
        ```
        This makes the expected structure clearer to mypy and runtime-safer.

3.  **Ensure Library PEP-561 Compliance**:
    The developers of `music_assistant` should ensure that the `music-assistant-client` library (version `1.2.0` or newer versions used by the integration) is fully type-hinted and includes a `py.typed` marker file in its distributed package. This is essential for `mypy` to correctly interpret types from the library.

4.  **Add to `.strict-typing` File**:
    Consider adding `music_assistant` to the `.strict-typing` file in the `home-assistant/core` repository. This will enable the strictest set of `mypy` checks for the integration's code during Home Assistant's CI, helping to catch more potential typing issues.

By addressing these points, the integration will better adhere to the `strict-typing` rule, leading to more robust and maintainable code.

_Created at 2025-05-14 11:55:31. Prompt tokens: 29988, Output tokens: 2159, Total tokens: 36960_
