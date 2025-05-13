# music_assistant: entity-device-class

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [entity-device-class](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-device-class)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `entity-device-class` rule requires that entities use device classes where possible to provide context for Home Assistant's UI, voice control, and cloud integrations.

This rule **applies** to the `music_assistant` integration because it creates `media_player` entities, and there are defined `MediaPlayerDeviceClass` options available in Home Assistant (e.g., `SPEAKER`, `TV`, `RECEIVER`).

The `music_assistant` integration **follows** this rule.
The primary entity created by this integration is `MusicAssistantPlayer` found in `homeassistant/components/music_assistant/media_player.py`.
In the `__init__` method of the `MusicAssistantPlayer` class, the device class is explicitly set:

```python
# homeassistant/components/music_assistant/media_player.py
# ...
from homeassistant.components.media_player import (
    # ...
    MediaPlayerDeviceClass,
    # ...
)
# ...

class MusicAssistantPlayer(MusicAssistantEntity, MediaPlayerEntity):
    """Representation of MediaPlayerEntity from Music Assistant Player."""

    # ...

    def __init__(self, mass: MusicAssistantClient, player_id: str) -> None:
        """Initialize MediaPlayer entity."""
        super().__init__(mass, player_id)
        self._attr_icon = self.player.icon.replace("mdi-", "mdi:")
        self._set_supported_features()
        self._attr_device_class = MediaPlayerDeviceClass.SPEAKER  # <-- Rule followed here
        self._prev_time: float = 0
    # ...
```

The code sets `self._attr_device_class = MediaPlayerDeviceClass.SPEAKER`. This is an appropriate and valid device class for a media player entity that primarily handles audio playback, as is the case with Music Assistant players. The integration only defines the `MEDIA_PLAYER` platform (as seen in `homeassistant/components/music_assistant/__init__.py`: `PLATFORMS = [Platform.MEDIA_PLAYER]`), so this check covers all entities created by the integration.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:18:29. Prompt tokens: 30097, Output tokens: 588, Total tokens: 32393_
