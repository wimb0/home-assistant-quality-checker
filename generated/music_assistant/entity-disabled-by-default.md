# music_assistant: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default)                                                     |
| Status | **exempt**                                       |
| Reason | The integration only creates `media_player` entities, which are core to its functionality and not "less popular" or "noisy" diagnostic-style entities that this rule targets. |

## Overview

The `entity-disabled-by-default` rule states that "less popular or noisy entities" should be disabled by default to save resources for users who may not need them. The primary example given is a diagnostic sensor like signal strength.

This rule does not apply to the `music_assistant` integration because it exclusively creates `media_player` entities. This is evident from the `PLATFORMS` constant in `homeassistant/components/music_assistant/__init__.py`:
```python
PLATFORMS = [Platform.MEDIA_PLAYER]
```
The integration sets up entities based on this platform in `async_setup_entry`. The `homeassistant/components/music_assistant/media_player.py` file defines `MusicAssistantPlayer`, which inherits from `MediaPlayerEntity`. These `media_player` entities represent the actual Music Assistant players and are the core, primary functional components of the integration.

These `media_player` entities are not "less popular" within the context of this integration; they are essential for its operation. Users installing the `music_assistant` integration explicitly want to control these players. Disabling them by default would render the integration non-functional until users manually enable them, which is counter-intuitive for primary entities.

Furthermore, while `media_player` entities do change state, these changes (e.g., play, pause, track change, volume change) are typically significant and often user-initiated. This is different from the "noisy" entities the rule describes, such as a sensor reporting signal strength every few seconds.

The rule is intended to apply to secondary, diagnostic, or auxiliary entities that might not be useful to all users. Since `music_assistant` currently only provides primary `media_player` entities and no such secondary entities, the rule is considered not applicable. If the integration were to add, for example, sensor entities for detailed player diagnostics (e.g., buffer status, sync accuracy, error rates), those would be candidates for being disabled by default according to this rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:18:57. Prompt tokens: 30162, Output tokens: 592, Total tokens: 32664_
