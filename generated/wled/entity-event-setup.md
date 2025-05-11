# wled: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **done**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `entity-event-setup` rule mandates that entities subscribing to events (e.g., from an integration library or other event sources like a `DataUpdateCoordinator`) must do so within the `async_added_to_hass` entity method. Correspondingly, they must unsubscribe from these events in `async_will_remove_from_hass`. The rule highlights `self.async_on_remove()` as a simplified and preferred way to manage unsubscriptions.

This rule applies to the `wled` integration as its entities react to data updates, which are effectively events, primarily from `DataUpdateCoordinator` instances.

The `wled` integration correctly follows this rule:

1.  **Primary Coordinator Updates:** All WLED entities inherit from `WLEDEntity`, which in turn inherits from `CoordinatorEntity`. The `CoordinatorEntity` base class correctly handles the subscription to the primary `DataUpdateCoordinator` within its own `async_added_to_hass` method, using `self.async_on_remove()` to register the listener removal. This ensures that all WLED entities automatically adhere to the rule for their main data source.

    ```python
    # Snippet from homeassistant.helpers.update_coordinator.CoordinatorEntity
    # WLEDEntity inherits this behavior.
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self._handle_coordinator_update, self.coordinator_context
            )
        )
    ```

2.  **Additional Coordinator Subscription (`WLEDUpdateEntity`):** The `WLEDUpdateEntity` in `update.py` subscribes to updates from a secondary coordinator, `WLEDReleasesDataUpdateCoordinator`. This subscription is correctly set up in `async_added_to_hass` and uses `self.async_on_remove()` for cleanup, perfectly aligning with the rule's example and requirements.

    In `update.py`:
    ```python
    class WLEDUpdateEntity(WLEDEntity, UpdateEntity):
        # ...
        def __init__(
            self,
            coordinator: WLEDDataUpdateCoordinator,
            releases_coordinator: WLEDReleasesDataUpdateCoordinator,
        ) -> None:
            """Initialize the update entity."""
            super().__init__(coordinator=coordinator) # Primary coordinator
            self.releases_coordinator = releases_coordinator # Secondary coordinator
        
        async def async_added_to_hass(self) -> None:
            """When entity is added to hass.

            Register extra update listener for the releases coordinator.
            """
            await super().async_added_to_hass() # Handles primary coordinator subscription via CoordinatorEntity
            self.async_on_remove(
                self.releases_coordinator.async_add_listener(
                    self._handle_coordinator_update # Method from CoordinatorEntity
                )
            )
    ```
    The `_handle_coordinator_update` method, inherited from `CoordinatorEntity`, is responsible for calling `self.async_write_ha_state()` when new data is received.

No other direct event subscriptions by entities that would violate this rule were found. Platform-level listeners (like `async_update_segments` in various platform files) that manage the addition/removal of entities based on coordinator updates are distinct from individual entities subscribing to events for their own state updates and are thus outside the direct scope of this rule's application to entity lifecycle methods.

Therefore, the `wled` integration adheres to the `entity-event-setup` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:27:11. Prompt tokens: 21987, Output tokens: 932, Total tokens: 25673_
