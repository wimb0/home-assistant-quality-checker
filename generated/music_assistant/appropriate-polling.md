# music_assistant: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **exempt**                                       |
| Reason | The integration is push-based (iot_class: local_push) and utilizes an event-driven mechanism for updates, rather than polling. Entities explicitly set `_attr_should_poll = False`. |

## Overview

The `appropriate-polling` rule requires integrations that poll for data to set a sensible polling interval. This rule does not apply to the `music_assistant` integration because it is primarily a push-based integration.

1.  **Manifest Declaration**: The `manifest.json` file declares `music_assistant` with `"iot_class": "local_push"`. This indicates that the integration receives updates from the device/service rather than actively polling it.

    ```json
    // homeassistant/components/music_assistant/manifest.json
    {
      "domain": "music_assistant",
      "name": "Music Assistant",
      // ...
      "iot_class": "local_push",
      // ...
    }
    ```

2.  **Event-Driven Updates**: The integration establishes a connection to the Music Assistant server and listens for events.
    In `homeassistant/components/music_assistant/__init__.py`, the `_client_listen` function calls `await mass.start_listening(init_ready)`. This function, part of the `music-assistant-client` library, is responsible for maintaining a connection and receiving real-time updates from the server.

    ```python
    // homeassistant/components/music_assistant/__init__.py
    async def _client_listen(
        hass: HomeAssistant,
        entry: ConfigEntry,
        mass: MusicAssistantClient,
        init_ready: asyncio.Event,
    ) -> None:
        """Listen with the client."""
        try:
            await mass.start_listening(init_ready)
        # ...
    ```

3.  **Entity Configuration**: The base entity class `MusicAssistantEntity` in `homeassistant/components/music_assistant/entity.py` explicitly sets `_attr_should_poll = False`. This disables Home Assistant's default polling mechanism for entities derived from this class.

    ```python
    // homeassistant/components/music_assistant/entity.py
    class MusicAssistantEntity(Entity):
        _attr_has_entity_name = True
        _attr_should_poll = False 
        # ...
    ```
    Instead of polling, entities subscribe to specific events from the Music Assistant client (`self.mass.subscribe`) and update their state when an event is received via the `__on_mass_update` callback.

    ```python
    // homeassistant/components/music_assistant/entity.py
    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await self.async_on_update()
        self.async_on_remove(
            self.mass.subscribe(
                self.__on_mass_update, EventType.PLAYER_UPDATED, self.player_id
            )
        )
        self.async_on_remove(
            self.mass.subscribe(
                self.__on_mass_update,
                EventType.QUEUE_UPDATED,
            )
        )

    async def __on_mass_update(self, event: MassEvent) -> None:
        """Call when we receive an event from MusicAssistant."""
        # ...
        await self.async_on_update()
        self.async_write_ha_state()
    ```

The rule `appropriate-polling` specifically targets integrations that implement polling, for which it provides guidance on setting `update_interval` for `DataUpdateCoordinator` or `SCAN_INTERVAL` for entities with `should_poll = True`. Since `music_assistant` does not use these polling mechanisms for its primary data updates and instead relies on a push-based architecture, the rule is not applicable.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 09:58:45. Prompt tokens: 30268, Output tokens: 969, Total tokens: 33461_
