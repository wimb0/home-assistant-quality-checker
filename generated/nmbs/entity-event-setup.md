# nmbs: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration's entities are polling-based and do not subscribe to events from an external library, which is the scenario this rule addresses. |

## Overview

The `entity-event-setup` rule dictates that entities subscribing to events from an integration library must set up these subscriptions in `async_added_to_hass` and tear them down in `async_will_remove_from_hass` (or use `async_on_remove`). This ensures proper lifecycle management and prevents memory leaks or errors from accessing `self.hass` prematurely.

This rule does not apply to the `nmbs` integration. The entities provided by this integration, `NMBSSensor` and `NMBSLiveBoard` (defined in `sensor.py`), operate on a polling basis. They fetch data from the `pyrail` API client during their `async_update` method:

*   `NMBSSensor.async_update` calls `self._api_client.get_connections(...)`.
*   `NMBSLiveBoard.async_update` calls `self._api_client.get_liveboard(...)`.

There is no indication in the code that these entities subscribe to any asynchronous events emitted by the `pyrail` library or any other external event source. The `pyrail` library is used for direct, request-response API calls. Consequently, the entities do not implement `async_added_to_hass` or `async_will_remove_from_hass` for event subscription management, as this pattern is not relevant to their design.

Since the entities do not subscribe to external library events, the requirements of the `entity-event-setup` rule are not applicable.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:21:39. Prompt tokens: 10245, Output tokens: 473, Total tokens: 12106_
