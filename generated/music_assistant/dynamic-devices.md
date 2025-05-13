# music_assistant: dynamic-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [dynamic-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `dynamic-devices` rule requires that an integration automatically discovers and adds entities for new devices that become available *after* the initial setup of the integration, without requiring a manual reload or restart.

This rule applies to the `music_assistant` integration because it manages Music Assistant players, which can be added or configured on the Music Assistant server at any time. These players should then automatically appear as `media_player` entities in Home Assistant.

The `music_assistant` integration correctly follows this rule. It employs an event-driven mechanism to listen for new players:

1.  **Initial Setup:** During `async_setup_entry` in `media_player.py`, any players already known to the Music Assistant server are added:
    ```python
    # homeassistant/components/music_assistant/media_player.py
    # add all current players
    for player in mass.players:
        if not player.expose_to_ha:
            continue
        added_ids.add(player.player_id)
        mass_players.append(MusicAssistantPlayer(mass, player.player_id))

    async_add_entities(mass_players)
    ```

2.  **Dynamic Discovery:** The integration subscribes to `EventType.PLAYER_ADDED` events from the `music-assistant-client`. When a new player is added on the Music Assistant server and this event is received, the `handle_player_added` callback is triggered.
    ```python
    # homeassistant/components/music_assistant/media_player.py
    async def handle_player_added(event: MassEvent) -> None:
        """Handle Mass Player Added event."""
        if TYPE_CHECKING:
            assert event.object_id is not None
        if event.object_id in added_ids: # known_devices check
            return
        player = mass.players.get(event.object_id)
        if TYPE_CHECKING:
            assert player is not None
        if not player.expose_to_ha:
            return
        added_ids.add(event.object_id) # update known_devices
        async_add_entities([MusicAssistantPlayer(mass, event.object_id)]) # add new entity

    # register listener for new players
    entry.async_on_unload(mass.subscribe(handle_player_added, EventType.PLAYER_ADDED))
    ```
    This `handle_player_added` function checks if the player is already known (using the `added_ids` set, analogous to `known_devices` in the rule's example) and if it should be exposed to Home Assistant. If so, it calls `async_add_entities` to create the new `MusicAssistantPlayer` entity.

This event-driven approach ensures that new players configured in Music Assistant are automatically detected and their corresponding entities are created in Home Assistant without user intervention, fully satisfying the `dynamic-devices` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:17:32. Prompt tokens: 30255, Output tokens: 768, Total tokens: 33093_
