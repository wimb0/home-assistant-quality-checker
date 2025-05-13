# music_assistant: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-event-setup` rule mandates that entities subscribing to external events (e.g., from an integration's library) must set up these subscriptions within their `async_added_to_hass` method and tear them down within `async_will_remove_from_hass`. The use of `self.async_on_remove` within `async_added_to_hass` is the recommended way to achieve this, as it ensures the unsubscription callback is correctly handled upon entity removal.

This rule applies to the `music_assistant` integration because its entities (`MusicAssistantEntity` and `MusicAssistantPlayer`) subscribe to events originating from the `music-assistant-client` library (`MassEvent`).

The integration **fully follows** this rule.

1.  **Subscription in `async_added_to_hass`**:
    *   The base entity `MusicAssistantEntity` (in `homeassistant/components/music_assistant/entity.py`) subscribes to `EventType.PLAYER_UPDATED` and `EventType.QUEUE_UPDATED` within its `async_added_to_hass` method.
        ```python
        # homeassistant/components/music_assistant/entity.py
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
        ```
    *   The `MusicAssistantPlayer` entity (in `homeassistant/components/music_assistant/media_player.py`), which inherits from `MusicAssistantEntity`, also subscribes to `EventType.QUEUE_TIME_UPDATED` and `EventType.PLAYER_CONFIG_UPDATED` within its own `async_added_to_hass` method. It correctly calls `await super().async_added_to_hass()` to ensure the base class subscriptions are also set up.
        ```python
        # homeassistant/components/music_assistant/media_player.py
        async def async_added_to_hass(self) -> None:
            """Register callbacks."""
            await super().async_added_to_hass()

            # ... (definition of queue_time_updated callback)
            self.async_on_remove(
                self.mass.subscribe(
                    queue_time_updated,
                    EventType.QUEUE_TIME_UPDATED,
                )
            )

            # ... (definition of player_config_changed callback)
            self.async_on_remove(
                self.mass.subscribe(
                    player_config_changed, EventType.PLAYER_CONFIG_UPDATED, self.player_id
                )
            )
        ```

2.  **Unsubscription using `async_on_remove`**:
    Both entities correctly use `self.async_on_remove()` when subscribing. This helper ensures that the unsubscribe function returned by `self.mass.subscribe()` is automatically called when the entity is removed (i.e., during `async_will_remove_from_hass`), preventing memory leaks.

3.  **Safe Callback Execution**:
    The event callbacks (`__on_mass_update` in `MusicAssistantEntity`, and `queue_time_updated`, `player_config_changed` in `MusicAssistantPlayer`) are only invoked after `async_added_to_hass` has completed and the entity is fully registered with Home Assistant. Therefore, calls to methods like `self.async_write_ha_state()` or accessing `self.hass` within these callbacks are safe and occur at the correct point in the entity lifecycle.

The implementation aligns with the best practices outlined in the rule description and its examples.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:01:59. Prompt tokens: 30283, Output tokens: 1005, Total tokens: 35261_
