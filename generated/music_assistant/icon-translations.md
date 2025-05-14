# music_assistant: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `icon-translations` rule requires integrations to define entity icons using a translation key that references an `icons.json` file, rather than setting the `_attr_icon` directly in the Python code. This approach helps to relieve the state machine by having the frontend look up the icon based on the key.

This rule applies to the `music_assistant` integration because it defines `MediaPlayerEntity` instances (specifically, `MusicAssistantPlayer` in `media_player.py`).

The integration currently does **NOT** follow this rule.
1.  **Direct Icon Assignment:** The `MusicAssistantPlayer` entity sets its icon directly using `self._attr_icon` in its `__init__` method:
    ```python
    # homeassistant/components/music_assistant/media_player.py
    class MusicAssistantPlayer(MusicAssistantEntity, MediaPlayerEntity):
        # ...
        def __init__(self, mass: MusicAssistantClient, player_id: str) -> None:
            # ...
            self._attr_icon = self.player.icon.replace("mdi-", "mdi:")
            # ...
    ```
    This bypasses the icon translation mechanism.

2.  **`icons.json` Structure:** The integration has an `icons.json` file (`homeassistant/components/music_assistant/icons.json`), but it only defines icons for services, not for entities. For entity icon translations, it would need an `entity` key with mappings for entity domains (like `media_player`) and their translation keys.
    Current `icons.json`:
    ```json
    {
      "services": {
        "play_media": { "service": "mdi:play" },
        // ... other services
      }
    }
    ```

While the entity sets `_attr_device_class = MediaPlayerDeviceClass.SPEAKER` (which provides a default icon), the integration correctly overrides this with a more specific icon derived from `self.player.icon` (e.g., `mdi:cast` for a Cast device). The issue is not *whether* to use a custom icon, but *how* that custom icon is provided to Home Assistant. The `icon-translations` rule mandates using translation keys for this.

## Suggestions

To make the `music_assistant` integration compliant with the `icon-translations` rule, the following changes are recommended:

1.  **Modify `MusicAssistantPlayer` to use `_attr_translation_key`:**
    Instead of setting `self._attr_icon` directly, set `self._attr_translation_key`. The key can be derived from `self.player.icon`, which provides an MDI icon string like "mdi-speaker" or "mdi-cast".

    Example modification in `homeassistant/components/music_assistant/media_player.py`:
    ```python
    class MusicAssistantPlayer(MusicAssistantEntity, MediaPlayerEntity):
        # ...
        def __init__(self, mass: MusicAssistantClient, player_id: str) -> None:
            """Initialize MediaPlayer entity."""
            super().__init__(mass, player_id)
            
            # Determine the translation key based on the player's icon string
            # A prefix can help avoid collisions and clarify the key's purpose.
            key_prefix = "player_icon_"
            raw_player_icon_name = self.player.icon  # e.g., "mdi-speaker", "mdi-cast"
            
            if raw_player_icon_name and raw_player_icon_name.startswith("mdi-"):
                # Use the part after "mdi-" as the specific part of the key
                # e.g., "mdi-speaker" -> "player_icon_speaker"
                self._attr_translation_key = key_prefix + raw_player_icon_name[4:]
            else:
                # Fallback to a default key if the icon name is unexpected
                self._attr_translation_key = key_prefix + "default"
                
            self._set_supported_features() # Existing call
            self._attr_device_class = MediaPlayerDeviceClass.SPEAKER # Existing attribute
            self._prev_time: float = 0 # Existing attribute
            # ...
    ```

2.  **Update `icons.json` to include entity icon translations:**
    Add an `entity` section to `homeassistant/components/music_assistant/icons.json` to map the translation keys (defined above) to their corresponding MDI icon strings. The existing `services` section should be kept.

    Example `icons.json` structure:
    ```json
    {
      "entity": {
        "media_player": {
          "player_icon_speaker": {
            "default": "mdi:speaker"
          },
          "player_icon_cast": {
            "default": "mdi:cast"
          },
          "player_icon_cast-audio": {
            "default": "mdi:cast-audio"
          },
          "player_icon_speaker-multiple": { 
            "default": "mdi:speaker-multiple"
          },
          "player_icon_default": { 
            "default": "mdi:speaker" 
          }
          // Add other keys for all possible icons returned by self.player.icon
          // from various Music Assistant player providers.
        }
      },
      "services": {
        "play_media": { "service": "mdi:play" },
        "play_announcement": { "service": "mdi:bullhorn" },
        "transfer_queue": { "service": "mdi:transfer" },
        "search": { "service": "mdi:magnify" },
        "get_queue": { "service": "mdi:playlist-music" },
        "get_library": { "service": "mdi:music-box-multiple" }
      }
    }
    ```
    The developer will need to identify all unique icon strings that `self.player.icon` can return across different Music Assistant player providers (e.g., "mdi-speaker", "mdi-cast", "mdi-cast-audio", "mdi-speaker-multiple", etc.) and create corresponding entries in `icons.json`.

**Why these changes satisfy the rule:**
*   By setting `_attr_translation_key`, the integration no longer sends the full icon string with the entity's state. Instead, it sends a compact key.
*   The frontend uses this key to look up the actual MDI icon from the `icons.json` file.
*   This aligns with the rule's goal of "relieving the state machine" and centralizing icon definitions in the `icons.json` file.

_Created at 2025-05-14 13:44:19. Prompt tokens: 30170, Output tokens: 1605, Total tokens: 38560_
