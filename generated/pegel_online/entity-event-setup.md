```markdown
# pegel_online: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration uses a `DataUpdateCoordinator` pattern for fetching data, and entities inherit from `CoordinatorEntity`. Entities do not subscribe directly to external events from the underlying library (`aiopegelonline`). |

## Overview

The `entity-event-setup` rule requires that entities subscribing to events from an external library or source do so within the `async_added_to_hass` method and unsubscribe within `async_will_remove_from_hass`, ideally using `self.async_on_remove`.

Analyzing the `pegel_online` integration code, specifically `homeassistant/components/pegel_online/coordinator.py` and `homeassistant/components/pegel_online/sensor.py`:

1.  The integration uses a `DataUpdateCoordinator` (`PegelOnlineDataUpdateCoordinator`) to fetch data from the `aiopegelonline` library at regular intervals (`MIN_TIME_BETWEEN_UPDATES`). This is implemented in the `_async_update_data` method of the coordinator (`homeassistant/components/pegel_online/coordinator.py`, line 39).
2.  The sensor entities (`PegelOnlineSensor`) inherit from `CoordinatorEntity` (`homeassistant/components/pegel_online/sensor.py`, line 90).
3.  `CoordinatorEntity` is designed to automatically handle the subscription of the entity to coordinator updates. When the coordinator updates its data, the entity's `_handle_coordinator_update` method is called. The base `CoordinatorEntity` class handles attaching and detaching from the coordinator within its own `async_added_to_hass` and `async_will_remove_from_hass` methods.
4.  The `pegel_online` entities (`PegelOnlineSensor`) do not override `async_added_to_hass` or `async_will_remove_from_hass` to perform any manual event subscriptions. They rely entirely on the `CoordinatorEntity` base class and the coordinator for data updates.

Since the entities obtain their state updates by listening to the `DataUpdateCoordinator` rather than subscribing directly to events provided by the `aiopegelonline` library, the `entity-event-setup` rule, which governs how entities manage *direct external event subscriptions*, does not apply to this integration's design.

## Suggestions

No suggestions needed. The integration uses a `DataUpdateCoordinator` pattern, which is a standard and recommended way to handle data updates from polling-based APIs in Home Assistant, and `CoordinatorEntity` correctly manages the entity's lifecycle connection to the coordinator.
```

_Created at 2025-05-25 11:22:13. Prompt tokens: 6064, Output tokens: 669, Total tokens: 7356_
