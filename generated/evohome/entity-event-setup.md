# evohome: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-event-setup` rule requires that entities subscribing to events (e.g., from an integration library or internal Home Assistant mechanisms like the dispatcher) do so in the `async_added_to_hass` method and unsubscribe in the `async_will_remove_from_hass` method, or use the `self.async_on_remove()` helper for cleanup. This ensures that resources are correctly managed throughout the entity's lifecycle, preventing memory leaks and other potential issues.

This rule applies to the `evohome` integration. Specifically, the base entity class `EvoEntity` in `homeassistant/components/evohome/entity.py` subscribes to dispatcher signals within its `async_added_to_hass` method:

```python
# homeassistant/components/evohome/entity.py
class EvoEntity(CoordinatorEntity[EvoDataUpdateCoordinator]):
    # ...
    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        async_dispatcher_connect(self.hass, DOMAIN, self.process_signal) # Subscription occurs here
    # ...
```

The `async_dispatcher_connect` function is a form of event subscription. While the subscription is correctly initiated in `async_added_to_hass`, the integration does not implement the corresponding unsubscription. The callable returned by `async_dispatcher_connect` (which is used to disconnect the signal) is not stored and called in `async_will_remove_from_hass`. Furthermore, the simplified `self.async_on_remove()` helper, which is designed for this purpose, is not used.

Failure to unregister these signal listeners can lead to callbacks being invoked on entities that have been removed or are no longer valid, potentially causing errors or memory leaks.

Therefore, the `evohome` integration does not fully follow the `entity-event-setup` rule due to the missing unsubscription mechanism for dispatcher signals.

## Suggestions

To make the `evohome` integration compliant with the `entity-event-setup` rule, the dispatcher connection made in `EvoEntity.async_added_to_hass` should be properly cleaned up when the entity is removed. This can be achieved by using the `self.async_on_remove()` helper method.

Modify the `async_added_to_hass` method in `homeassistant/components/evohome/entity.py` as follows:

```python
# homeassistant/components/evohome/entity.py
from homeassistant.helpers.dispatcher import async_dispatcher_connect # Ensure this import is present or adjust as needed

# ... other imports ...

class EvoEntity(CoordinatorEntity[EvoDataUpdateCoordinator]):
    # ... (other parts of the class) ...

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Use self.async_on_remove to ensure the dispatcher connection is cleaned up
        self.async_on_remove(
            async_dispatcher_connect(self.hass, DOMAIN, self.process_signal)
        )

    # ... (rest of the class) ...
```

**Why this change satisfies the rule:**

By wrapping the call to `async_dispatcher_connect` with `self.async_on_remove()`, Home Assistant will automatically call the unsubscribe function returned by `async_dispatcher_connect` when the entity is removed from Home Assistant (i.e., when `async_will_remove_from_hass` would be involved). This fulfills the requirement to unsubscribe from events to prevent memory leaks and ensure proper lifecycle management, as outlined in the `entity-event-setup` rule. This is the recommended and cleaner way to handle such resource cleanup for entities.

---

_Created at 2025-05-29 11:43:28. Prompt tokens: 21998, Output tokens: 976, Total tokens: 25398._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
