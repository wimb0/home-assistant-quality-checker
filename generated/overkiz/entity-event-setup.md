# overkiz: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **done**                                                                 |

## Overview

The `entity-event-setup` rule mandates that if entities need to subscribe to events (e.g., from an integration library or the Home Assistant event bus), these subscriptions must be set up in the `async_added_to_hass` entity method and cleaned up in `async_will_remove_from_hass` (or by using `self.async_on_remove` within `async_added_to_hass`). This ensures proper lifecycle management, preventing errors and memory leaks.

This rule applies to the `overkiz` integration. The integration's entities primarily inherit from `OverkizEntity` or `OverkizDescriptiveEntity`, which are subclasses of Home Assistant's `CoordinatorEntity`. `CoordinatorEntity` instances subscribe to updates from their respective `DataUpdateCoordinator`. This subscription is a form of event listening.

The `overkiz` integration follows this rule because:

1.  **CoordinatorEntity Compliance**: The `CoordinatorEntity` base class correctly handles its subscription to coordinator updates. As seen in `homeassistant/helpers/update_coordinator.py`, `CoordinatorEntity.async_added_to_hass` uses `self.async_on_remove` to register a listener for coordinator updates:
    ```python
    # homeassistant/helpers/update_coordinator.py
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self._handle_coordinator_update, self.coordinator_context
            )
        )
        # ...
    ```
    This adheres to the best practice outlined in the rule for managing subscription lifecycles. Since all `overkiz` entities (except `OverkizScene`) derive from `CoordinatorEntity` (via `OverkizEntity`), they inherit this correct behavior for their primary mode of receiving updates.

2.  **No Other Direct Entity Subscriptions Found**: A review of the `overkiz` entity code (e.g., in `sensor.py`, `cover/generic_cover.py`, `light.py`, etc.) did not reveal any instances where entities make *additional* direct subscriptions to events from the `pyoverkiz` library or the Home Assistant event bus. Event handling from the `pyoverkiz` library (e.g., device state changes) is managed by the `OverkizDataUpdateCoordinator` (in `coordinator.py`). The coordinator fetches and processes these events, and entities are updated through the standard coordinator mechanism.
    For example, in `homeassistant/components/overkiz/entity.py`, neither `OverkizEntity` nor `OverkizDescriptiveEntity` override `async_added_to_hass` or `async_will_remove_from_hass` to add custom event subscriptions.

3.  **`OverkizScene` Entity**: The `homeassistant/components/overkiz/scene.py` defines `OverkizScene`, which inherits directly from `homeassistant.components.scene.Scene` and not `CoordinatorEntity`. This entity handles scene activation and does not appear to subscribe to any events. Therefore, the subscription management aspect of this rule is not applicable to `OverkizScene` in a way that would indicate non-compliance.

In summary, the event subscriptions that `overkiz` entities make (to their coordinator) are handled correctly according to their lifecycle by the `CoordinatorEntity` base class. There are no other identified event subscriptions within the entities themselves that would require custom handling under this rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:10:56. Prompt tokens: 87168, Output tokens: 909, Total tokens: 93166_
