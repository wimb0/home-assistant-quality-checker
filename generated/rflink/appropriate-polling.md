# rflink: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [rflink](https://www.home-assistant.io/integrations/rflink/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **exempt**                                       |
| Reason | The RFLink integration is primarily event-driven (push-based) for receiving device updates and does not use a polling mechanism that this rule targets. |

## Overview

The `appropriate-polling` rule mandates that integrations relying on polling to fetch data must define a suitable polling interval. This ensures responsible use of resources, especially for cloud services or battery-operated devices.

This rule does **not apply** to the `rflink` integration. The `rflink` integration interfaces with an RFLink gateway (connected via serial or TCP), which in turn communicates with various RF (Radio Frequency) devices (e.g., 433MHz sensors, switches, remotes).

The primary mechanism for receiving device state updates in the `rflink` integration is event-driven or push-based:
1.  RF devices transmit their state or commands.
2.  The RFLink gateway receives these transmissions.
3.  The RFLink gateway sends this data as an event to Home Assistant over the established connection.
4.  The Home Assistant `rflink` integration processes these incoming events and updates the corresponding entities.

Key indicators in the code supporting this:
*   **No Active Polling by Entities:** The base entity class `RflinkDevice` in `homeassistant/components/rflink/entity.py` explicitly sets `_attr_should_poll = False` (line 30). This means Home Assistant's core entity polling mechanism is not used for these entities.
    ```python
    # homeassistant/components/rflink/entity.py
    class RflinkDevice(Entity):
        # ...
        _attr_should_poll = False
        # ...
    ```
*   **Event-Driven Updates:** In `homeassistant/components/rflink/__init__.py`, an `event_callback` function (defined around line 103) is passed to the `rflink` library's `create_rflink_connection` method. This callback is invoked by the library whenever the RFLink gateway sends new data (events).
    ```python
    # homeassistant/components/rflink/__init__.py
    # ...
    @callback
    def event_callback(event):
        """Handle incoming Rflink events."""
        # ...
        async_dispatcher_send(hass, SIGNAL_EVENT, event_data) # Simplified for illustration
    # ...
    connection = create_rflink_connection(
        # ...
        event_callback=event_callback,
        # ...
    )
    # ...
    ```
    These events are then dispatched to the relevant entities, which update their state accordingly.
*   **No `DataUpdateCoordinator` for Polling:** The integration does not use a `DataUpdateCoordinator` with an `update_interval` to periodically fetch data from devices.
*   **No `SCAN_INTERVAL`:** Since `should_poll` is false, there's no `SCAN_INTERVAL` defined at the platform level for entities.

While the integration has a `CONF_RECONNECT_INTERVAL` (defined in `homeassistant/components/rflink/__init__.py`, line 66), this interval is for attempts to re-establish the connection to the RFLink gateway itself if it's lost, not for polling individual device states. Similarly, `CONF_KEEPALIVE_IDLE` is for maintaining TCP socket health.

Because the `rflink` integration relies on events pushed from the RFLink gateway rather than actively polling devices at a set interval for their state, the `appropriate-polling` rule is not applicable.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 13:24:07. Prompt tokens: 17894, Output tokens: 883, Total tokens: 20937_
