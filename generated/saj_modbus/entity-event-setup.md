# saj_modbus: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration uses the `DataUpdateCoordinator` pattern, and entities do not subscribe to external events. |

## Overview

The `entity-event-setup` rule requires that entities which subscribe to events (e.g., from a library) must do so within the `async_added_to_hass` lifecycle method and unsubscribe within `async_will_remove_from_hass`.

This rule does not apply to the `saj_modbus` integration. The integration uses a polling-based approach for data updates, which is managed by the Home Assistant `DataUpdateCoordinator`.

Specifically:
1.  The `SAJModbusHub` class in `hub.py` inherits from `DataUpdateCoordinator`. This hub is responsible for polling the SAJ inverter at a regular interval.
2.  The entities defined in `sensor.py` (`SajSensor`, `SajCounterSensor`) and `number.py` (`SajNumber`) all inherit from `CoordinatorEntity`.

The `CoordinatorEntity` base class handles the subscription to the coordinator's updates. It correctly implements `async_added_to_hass` to register for updates and `async_will_remove_from_hass` to unregister, abstracting this logic away from the integration's entity code.

Since the entities in `saj_modbus` get their data via the coordinator and do not subscribe to any other external, push-based events, there is no need for them to manually implement these lifecycle methods. The existing architecture correctly handles data updates, making this rule exempt.

## Suggestions

No suggestions needed.

---

_Created at 2025-06-11 21:32:25. Prompt tokens: 16838, Output tokens: 456, Total tokens: 18718._

_AI can be wrong. Always verify the report and the code against the rule._
