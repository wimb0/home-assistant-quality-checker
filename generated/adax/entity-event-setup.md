# adax: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration utilizes the `DataUpdateCoordinator` pattern. Entities are subclasses of `CoordinatorEntity` and do not subscribe to external events directly from the `adax` or `adax_local` client libraries; updates are polled by the coordinator. |

## Overview

The `entity-event-setup` rule mandates that entities subscribing to events (e.g., from an integration's client library) must manage these subscriptions within the `async_added_to_hass` method for setup and `async_will_remove_from_hass` (or `async_on_remove`) for teardown. This ensures proper lifecycle management and prevents errors or memory leaks.

This rule is **exempt** for the `adax` integration because its entities do not directly subscribe to events from the underlying `adax` or `adax_local` libraries in the manner described by the rule.

Here's why:
1.  **Coordinator-Based Updates:** The `adax` integration employs the `DataUpdateCoordinator` pattern for fetching data. It has `AdaxCloudCoordinator` and `AdaxLocalCoordinator` (defined in `coordinator.py`) which are responsible for polling the Adax cloud API or local devices using the `adax` and `adax_local` Python libraries respectively.
    *   `AdaxCloudCoordinator._async_update_data` calls `await self.adax_data_handler.get_rooms()`.
    *   `AdaxLocalCoordinator._async_update_data` calls `await self.adax_data_handler.get_status()`.
    These are polling operations, not event-driven callbacks from the library to the coordinator.

2.  **`CoordinatorEntity` Usage:** The climate entities (`AdaxDevice` and `LocalAdaxDevice` in `climate.py`) are subclasses of `CoordinatorEntity`.
    ```python
    # climate.py
    class AdaxDevice(CoordinatorEntity[AdaxCloudCoordinator], ClimateEntity):
        # ...

    class LocalAdaxDevice(CoordinatorEntity[AdaxLocalCoordinator], ClimateEntity):
        # ...
    ```
    The `CoordinatorEntity` base class in Home Assistant handles the "subscription" to updates from its associated coordinator. It uses `async_add_listener` within its own `async_added_to_hass` method and leverages `self.async_on_remove` to ensure the listener is removed when the entity is removed. This internal mechanism of `CoordinatorEntity` correctly follows the principles of the `entity-event-setup` rule for coordinator-sourced updates.

3.  **No Direct Library Event Subscriptions by Entities:** The `AdaxDevice` and `LocalAdaxDevice` entities do not make any additional, direct calls to subscribe to events from the `self._adax_data_handler` (which is an instance of the `adax` or `adax_local` library). The interaction with these libraries for data retrieval is managed by the coordinators. The libraries, as used by this integration, appear to be primarily request-response based rather than emitting events that entities would subscribe to directly. The `iot_class` in `manifest.json` is `local_polling`, further indicating a polling-based approach.

Since the entities rely on the `CoordinatorEntity` mechanism for updates and do not implement their own subscriptions to external library events, the specific scenario targeted by the `entity-event-setup` rule (i.e., an entity directly managing `client.events.subscribe()` or similar) is not present.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:05:43. Prompt tokens: 6828, Output tokens: 873, Total tokens: 11427_
