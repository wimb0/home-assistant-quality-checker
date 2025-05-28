```markdown
# fritzbox: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup) |
| Status | **exempt**                                                               |
| Reason | The integration uses a DataUpdateCoordinator for polling device state updates. Entities are CoordinatorEntity instances that rely on the coordinator's update mechanism, not direct event subscriptions from the underlying library. The only event listener found (EVENT_HOMEASSISTANT_STOP) is correctly managed using entry.async_on_unload in `__init__.py`. |

## Overview

The `entity-event-setup` rule mandates that Home Assistant entities which need to subscribe to external events (e.g., from an integration library) should perform the subscription setup within the entity's `async_added_to_hass` method and the cleanup/unsubscribe within `async_will_remove_from_hass` (or using `self.async_on_remove`). This ensures that the entity has access to necessary Home Assistant interfaces (`self.hass`, `self.async_write_ha_state`) when the callback is potentially triggered and prevents memory leaks upon entity removal.

Upon reviewing the `fritzbox` integration code, specifically the `coordinator.py` and the entity files (`entity.py`, `binary_sensor.py`, `cover.py`, `light.py`, `sensor.py`, `switch.py`, `button.py`), it is clear that the integration follows the `DataUpdateCoordinator` pattern.

The `FritzboxDataUpdateCoordinator` in `coordinator.py` handles polling the FRITZ!Box device using the `pyfritzhome` library at a set interval (`timedelta(seconds=30)`). It fetches device data via `self.fritz.update_devices()` in the `_update_fritz_devices` method.

The entities, such as `FritzboxBinarySensor`, `FritzboxCover`, etc., inherit from `FritzBoxDeviceEntity` or `FritzBoxEntity`, which in turn inherit from `CoordinatorEntity`. `CoordinatorEntity` instances automatically receive state updates when the associated coordinator's `async_update_listeners` method is called (which happens after a successful poll in `DataUpdateCoordinator`). These entities do not directly subscribe to events from the `pyfritzhome` library or elsewhere; their state is updated based on the data provided by the coordinator after a poll cycle.

The `pyfritzhome` library itself appears to be primarily a polling-based library, and there is no indication in the `fritzbox` integration code that it is utilizing any event push mechanisms from the library that would necessitate per-entity subscriptions.

The only event listener present in the integration is the `EVENT_HOMEASSISTANT_STOP` listener registered in `__init__.py`. This listener is not related to entity state updates but is used for logging out of the FRITZ!Box upon Home Assistant shutdown. This listener is correctly managed using `entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, logout_fritzbox))`, which correctly handles unsubscribing when the config entry is unloaded, following the spirit of the rule's lifecycle management principle.

Since the entities within the `fritzbox` integration do not subscribe to external events directly but rely on a polling coordinator, the rule `entity-event-setup` concerning the entity's lifecycle methods (`async_added_to_hass`, `async_will_remove_from_hass`) for managing subscriptions does not apply to this integration's current architecture.

```

_Created at 2025-05-25 11:20:07. Prompt tokens: 19159, Output tokens: 837, Total tokens: 20927_
