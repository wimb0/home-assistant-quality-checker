# music_assistant: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unique-id` rule requires that all entities created by an integration have a unique ID. This ID allows Home Assistant to track entities across restarts, enabling users to customize them (e.g., rename, assign to areas).

This rule applies to the `music_assistant` integration because it creates `MediaPlayerEntity` instances representing players managed by a Music Assistant server.

The `music_assistant` integration **fully follows** this rule.

Entities in this integration are based on the `MusicAssistantEntity` class, defined in `homeassistant/components/music_assistant/entity.py`. This base class provides a `unique_id` property:

```python
# homeassistant/components/music_assistant/entity.py
class MusicAssistantEntity(Entity):
    # ...
    @property
    def unique_id(self) -> str | None:
        """Return unique id for entity."""
        _base = self.player_id
        if hasattr(self, "entity_description"):
            return f"{_base}_{self.entity_description.key}"
        return _base
```

The `MusicAssistantPlayer` entity, defined in `homeassistant/components/music_assistant/media_player.py`, inherits from `MusicAssistantEntity`. During initialization, each entity instance is provided with a `player_id`:

```python
# homeassistant/components/music_assistant/entity.py
    def __init__(self, mass: MusicAssistantClient, player_id: str) -> None:
        """Initialize MediaPlayer entity."""
        self.mass = mass
        self.player_id = player_id
        # ...
```

This `player_id` is sourced from the Music Assistant server and represents the server's unique identifier for that specific player. The `unique_id` property then returns this `player_id` (or a derived version if an `entity_description` with a `key` is present, though for the main `MediaPlayerEntity` it effectively resolves to `player_id`).

Since `player_id` is unique for each player device within the Music Assistant server, it serves as a reliable unique identifier for the corresponding Home Assistant entity within the `music_assistant` integration's `media_player` platform. This ensures that each `MediaPlayerEntity` created by the integration has a distinct and persistent unique ID, satisfying the rule's requirements.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:02:40. Prompt tokens: 30017, Output tokens: 645, Total tokens: 33868_
