# music_assistant: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **todo**                                                                 |

## Overview

The `strict-typing` rule applies to the `music_assistant` integration. This rule emphasizes the use of comprehensive type hints to catch bugs early and improve code clarity, including the use of PEP-561 compliant libraries and adding the integration to Home Assistant Core's `.strict-typing` file. A key requirement is that if an integration uses `runtime_data` on a `ConfigEntry`, a custom typed `ConfigEntry` (e.g., `MyIntegrationConfigEntry = ConfigEntry[MyEntryData]`) must be defined and used consistently throughout the integration for functions handling that config entry.

The `music_assistant` integration defines a custom `ConfigEntry` type:
```python
# __init__.py
type MusicAssistantConfigEntry = ConfigEntry[MusicAssistantEntryData]

@dataclass
class MusicAssistantEntryData:
    """Hold Mass data for the config entry."""
    mass: MusicAssistantClient
    listen_task: asyncio.Task
```
And it utilizes `runtime_data` for storing `MusicAssistantEntryData`:
```python
# __init__.py
# store the listen task and mass client in the entry data
entry.runtime_data = MusicAssistantEntryData(mass, listen_task)
```

However, the integration does not consistently use `MusicAssistantConfigEntry` in all relevant function signatures.

**Violations found:**

1.  **Inconsistent `MusicAssistantConfigEntry` Usage:**
    The custom `MusicAssistantConfigEntry` type is not used in several functions that operate on the integration's config entry, even when these entries are expected to (or do) hold `runtime_data`.
    *   In `homeassistant/components/music_assistant/__init__.py`:
        *   The internal helper function `_client_listen` is defined as `async def _client_listen(hass: HomeAssistant, entry: ConfigEntry, ...) -> None:`. The `entry` parameter here is the integration's config entry (passed from `async_setup_entry` where it is correctly typed as `MusicAssistantConfigEntry`) and should be typed as `MusicAssistantConfigEntry`.
        *   The `async_unload_entry` function is defined as `async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:`. This function accesses `entry.runtime_data`, so `entry` must be typed as `MusicAssistantConfigEntry`.
        *   The `async_remove_config_entry_device` function is defined as `async def async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, ...) -> bool:`. The `config_entry` is used to retrieve the client, which involves accessing `runtime_data` indirectly via `get_music_assistant_client`. Thus, `config_entry` should be typed as `MusicAssistantConfigEntry`.

2.  **Use of `Any` where a more specific type is possible:**
    *   In `homeassistant/components/music_assistant/media_browser.py`:
        The `build_item` function has a parameter `media_class: Any`.
        ```python
        def build_item(
            mass: MusicAssistantClient,
            item: MediaItemType,
            can_expand: bool = True,
            media_class: Any = None, # <-- Should be more specific
        ) -> BrowseMedia:
        ```
        Given its usage (assigned `item.media_type.value` or values from `LIBRARY_MEDIA_CLASS_MAP`), a more specific type like `MediaClass | str | None` would be appropriate.

While the integration generally has good type hinting coverage and uses `from __future__ import annotations`, these specific omissions prevent it from fully complying with the `strict-typing` rule.

## Suggestions

To make the `music_assistant` integration compliant with the `strict-typing` rule, the following changes are recommended:

1.  **Consistently use `MusicAssistantConfigEntry`:**
    Update the type hints for `ConfigEntry` parameters to `MusicAssistantConfigEntry` in functions where the entry is known to be the one for this integration and potentially holds `runtime_data`.

    *   In `homeassistant/components/music_assistant/__init__.py`:
        *   Modify `_client_listen`:
            ```python
            # Before
            async def _client_listen(
                hass: HomeAssistant,
                entry: ConfigEntry, # <-- Incorrect type
                mass: MusicAssistantClient,
                init_ready: asyncio.Event,
            ) -> None:
            
            # After
            async def _client_listen(
                hass: HomeAssistant,
                entry: MusicAssistantConfigEntry, # <-- Correct type
                mass: MusicAssistantClient,
                init_ready: asyncio.Event,
            ) -> None:
            ```
        *   Modify `async_unload_entry`:
            ```python
            # Before
            async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool: # <-- Incorrect type
            
            # After
            async def async_unload_entry(hass: HomeAssistant, entry: MusicAssistantConfigEntry) -> bool: # <-- Correct type
            ```
        *   Modify `async_remove_config_entry_device`:
            ```python
            # Before
            async def async_remove_config_entry_device(
                hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry # <-- Incorrect type
            ) -> bool:

            # After
            async def async_remove_config_entry_device(
                hass: HomeAssistant, config_entry: MusicAssistantConfigEntry, device_entry: dr.DeviceEntry # <-- Correct type
            ) -> bool:
            ```
    *Why these changes satisfy the rule:* The rule explicitly requires the custom typed `ConfigEntry` (here, `MusicAssistantConfigEntry`) to be "used throughout" when `runtime_data` is implemented. Correcting these signatures ensures this consistency.

2.  **Refine `Any` types:**
    Replace `Any` with more specific types where possible.

    *   In `homeassistant/components/music_assistant/media_browser.py` for the `build_item` function:
        ```python
        # Before
        def build_item(
            mass: MusicAssistantClient,
            item: MediaItemType,
            can_expand: bool = True,
            media_class: Any = None, 
        ) -> BrowseMedia:

        # After (assuming MediaClass is an enum from homeassistant.components.media_player)
        from homeassistant.components.media_player import MediaClass # Ensure import

        def build_item(
            mass: MusicAssistantClient,
            item: MediaItemType,
            can_expand: bool = True,
            media_class: MediaClass | str | None = None, 
        ) -> BrowseMedia:
        ```
    *Why this change satisfies the rule:* Strict typing aims to make types as specific as reasonably possible, reducing ambiguity and potential for errors. `MediaClass | str | None` more accurately reflects the possible types for `media_class`.

3.  **Consider PEP-561 Compliance for `music-assistant-client`:**
    The rule recommends that external libraries used by the integration are fully typed and PEP-561 compliant (i.e., include a `py.typed` marker file). This allows `mypy` to effectively check interactions with the library. Investigate if the `music-assistant-client` library meets this, and if not, consider contributing type hints and the `py.typed` file to that project.

4.  **Add to Home Assistant Core's `.strict-typing` file:**
    Once the integration's internal typing is robust, consider adding `music_assistant` to the [`.strict-typing` file](https://github.com/home-assistant/core/blob/dev/.strict-typing) in the Home Assistant Core repository. This enables the strictest `mypy` checks for the integration's code within the HA development environment.

_Created at 2025-05-14 11:57:44. Prompt tokens: 29988, Output tokens: 1893, Total tokens: 36584_
