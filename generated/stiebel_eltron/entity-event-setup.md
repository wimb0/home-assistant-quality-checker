# stiebel_eltron: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration uses a polling mechanism for entity updates and does not subscribe to external library events. |

## Overview

The `entity-event-setup` rule mandates that if entities subscribe to events (e.g., from an external library) to update their state, these subscriptions must be managed within the `async_added_to_hass` (for subscribing) and `async_will_remove_from_hass` (for unsubscribing) lifecycle methods. This ensures that Home Assistant resources like `self.hass` are available and prevents memory leaks.

This rule does **not apply** to the `stiebel_eltron` integration. Here's why:

1.  **Polling Mechanism:** The integration is declared as `local_polling` in its `manifest.json`. This indicates that it primarily relies on periodically querying the device for updates.
2.  **Entity Update Logic:** The `StiebelEltron` climate entity, defined in `climate.py`, uses a synchronous `update()` method:
    ```python
    # homeassistant/components/stiebel_eltron/climate.py
    class StiebelEltron(ClimateEntity):
        # ...
        def update(self) -> None:
            """Update unit attributes."""
            self._client.update()  # Fetches data from the device

            self._target_temperature = self._client.get_target_temp()
            self._current_temperature = self._client.get_current_temp()
            # ... and so on
    ```
    This `update()` method is called by Home Assistant's entity update mechanism (typically on a schedule for polling entities) to refresh the entity's state. It actively fetches data rather than passively receiving it through an event callback.

3.  **No Event Subscription Code:** The `StiebelEltron` entity does not implement `async_added_to_hass` or `async_will_remove_from_hass` for managing event subscriptions. There are no calls to any event subscription methods (e.g., `self._client.events.subscribe(...)` or similar patterns as shown in the rule's example) from the `pystiebeleltron` library. The interaction with the library is through direct method calls like `self._client.update()` and `self._client.get_target_temp()`.

Since the `stiebel_eltron` entities do not subscribe to events from the underlying `pystiebeleltron` library or any other external event source, the requirements for setting up and tearing down event subscriptions within `async_added_to_hass` and `async_will_remove_from_hass` are not applicable. The integration follows a polling pattern, which is outside the scope of this specific rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 14:56:04. Prompt tokens: 6280, Output tokens: 717, Total tokens: 9580_
