# music_assistant: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `entity-unavailable` rule requires that an integration marks its entities as unavailable if it cannot fetch data from the corresponding device or service. If data can be fetched but some pieces are missing, the entity state should be marked as unknown (though for `MediaPlayerEntity`, this usually means relevant attributes are `None` while the entity remains available with a state like `IDLE` or `OFF`).

The `music_assistant` integration manages `MediaPlayerEntity` instances representing players controlled by a Music Assistant server. The availability of these entities is handled in the `MusicAssistantEntity` base class, specifically through its `available` property:

```python
# homeassistant/components/music_assistant/entity.py
class MusicAssistantEntity(Entity):
    # ...
    @property
    def available(self) -> bool:
        """Return availability of entity."""
        return self.player.available and bool(self.mass.connection.connected)
```

This implementation correctly addresses the rule's requirements:

1.  **Connection to the Service:** `bool(self.mass.connection.connected)` checks if the Home Assistant integration is currently connected to the Music Assistant server. If this connection is lost, all entities provided by this Music Assistant server instance will become unavailable. This is analogous to a `DataUpdateCoordinator` failing to update, which would cause `coordinator.last_update_success` to be `False`, and thus `super().available` in a `CoordinatorEntity` to return `False`.

2.  **Individual Device Availability:** `self.player.available` checks the availability of the specific player instance as reported by the Music Assistant server. The Music Assistant server itself is responsible for determining if it can communicate with and control the underlying physical player (e.g., a Sonos speaker, a Chromecast). If the Music Assistant server reports that a player is unavailable, the corresponding Home Assistant entity will also become unavailable. This is analogous to checking if specific data for an entity is present in the coordinator's data (e.g., `self.identifier in self.coordinator.data`).

During the setup phase (`async_setup_entry` in `homeassistant/components/music_assistant/__init__.py`), if a connection to the Music Assistant server cannot be established, `ConfigEntryNotReady` is raised. This prevents the entities from being set up in an unavailable state from the start and defers loading, which is the correct behavior.

If the connection to the Music Assistant server is lost after setup, the `_client_listen` background task in `__init__.py` will detect this. While the connection is lost, `self.mass.connection.connected` will be `False`, making entities unavailable. The task then attempts to reload the config entry, which will re-evaluate availability during the subsequent setup attempt.

The combination of these checks ensures that entities accurately reflect their availability based on both the connection to the central Music Assistant service and the status of the individual players managed by that service.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:09:44. Prompt tokens: 30357, Output tokens: 751, Total tokens: 33808_
