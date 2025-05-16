# linkplay: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration's entities primarily use a polling mechanism for state updates and do not subscribe to events from the `python-linkplay` library in the manner described by this rule. |

## Overview

The `entity-event-setup` rule mandates that entities subscribing to events (e.g., from an integration's underlying library) to update their state must manage these subscriptions within the `async_added_to_hass` and `async_will_remove_from_hass` lifecycle methods. This ensures that subscriptions are active only when the entity is part of Home Assistant and are cleaned up properly to prevent memory leaks.

This rule does not apply to the `linkplay` integration. The primary entities, such as `LinkPlayMediaPlayerEntity` in `media_player.py`, do not subscribe to an event stream from the `python-linkplay` library to receive state updates. Instead, they rely on a polling mechanism.

Specifically, `LinkPlayMediaPlayerEntity` implements an `async_update` method:
```python
# media_player.py
    @exception_wrap
    async def async_update(self) -> None:
        """Update the state of the media player."""
        try:
            await self._bridge.player.update_status()
            self._retry_count = 0
            self._update_properties()
        except LinkPlayRequestException:
            self._retry_count += 1
            if self._retry_count >= RETRY_POLL_MAXIMUM:
                self._attr_available = False
```
This method actively fetches the current status from the `LinkPlayBridge` (`self._bridge.player.update_status()`). This is a "pull" model of data retrieval, contrasting with the "push" model (event-driven) that the `entity-event-setup` rule addresses. The rule's example demonstrates a pattern like `self.client.events.subscribe("my_event", self._handle_event)`, which is not found in the `linkplay` entities for their state updates from the library.

While `LinkPlayMediaPlayerEntity` does implement `async_added_to_hass`, its purpose there is to register the entity with a shared data structure within the integration, not to subscribe to library events for state changes:
```python
# media_player.py
    async def async_added_to_hass(self) -> None:
        """Handle common setup when added to hass."""
        await super().async_added_to_hass()
        self.hass.data[DOMAIN][SHARED_DATA].entity_to_bridge[self.entity_id] = (
            self._bridge.device.uuid
        )
```
No corresponding `async_will_remove_from_hass` is implemented to unsubscribe from library events because no such subscription is established in `async_added_to_hass`.

Because the `linkplay` entities do not subscribe to events from the `python-linkplay` library for their primary state management, the specific lifecycle management requirements for such subscriptions (as detailed in the `entity-event-setup` rule) are not applicable.

## Suggestions
No suggestions needed.

_Created at 2025-05-11 07:10:34. Prompt tokens: 11399, Output tokens: 791, Total tokens: 15191_
