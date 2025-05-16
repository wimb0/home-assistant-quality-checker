# nmbs: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **todo**                                                                 |

## Overview

The `appropriate-polling` rule requires polling integrations to explicitly set a polling interval that is appropriate for the data being fetched and serves the majority of users, aiming to avoid unnecessary requests.

This rule applies to the `nmbs` integration:
1.  The `manifest.json` declares `iot_class: "cloud_polling"`, indicating it polls a cloud service.
2.  The sensor entities (`NMBSSensor` and `NMBSLiveBoard` in `sensor.py`) inherit from `SensorEntity` and implement an `async_update` method. This method is called periodically by Home Assistant to refresh the entity's state, signifying a polling mechanism.

The integration currently does NOT follow this rule because it does not explicitly define a polling interval for its sensor entities.
As seen in `sensor.py`, neither the `NMBSSensor` class nor the `NMBSLiveBoard` class, nor the module itself, defines the `SCAN_INTERVAL` constant.
```python
# sensor.py - Relevant snippets showing lack of SCAN_INTERVAL

# No SCAN_INTERVAL constant at the module level

class NMBSLiveBoard(SensorEntity):
    # ...
    async def async_update(self, **kwargs: Any) -> None:
        # Fetches data from self._api_client
        liveboard = await self._api_client.get_liveboard(self._station.id)
        # ...

class NMBSSensor(SensorEntity):
    # ...
    async def async_update(self, **kwargs: Any) -> None:
        # Fetches data from self._api_client
        connections = await self._api_client.get_connections(
            self._station_from.id, self._station_to.id
        )
        # ...
```
When `SCAN_INTERVAL` is not set for entities that poll, Home Assistant defaults to a standard interval (typically 30 seconds for `SensorEntity` subclasses with an `async_update` method). While this default might be acceptable for some use cases, the rule requires the integration to make a deliberate choice and *set* an appropriate interval. Relying on the HA default does not demonstrate this explicit consideration, especially concerning the iRail API's request to "be a good API citizen" and avoid querying too aggressively.

## Suggestions

To comply with the `appropriate-polling` rule, the integration should explicitly define a `SCAN_INTERVAL` for its polling sensor entities.

1.  **Define `SCAN_INTERVAL` in `sensor.py`:**
    Add a `SCAN_INTERVAL` constant at the module level in `homeassistant/components/nmbs/sensor.py`. A recommended value to start with is `timedelta(minutes=1)` (60 seconds). This interval is generally a good balance for data like train schedules/liveboards, reducing the load on the external API compared to the default 30 seconds, while still providing timely updates for most users. The iRail API documentation advises users to be "good API citizens" and avoid excessive requests, making a slightly longer, explicit interval more responsible.

    ```python
    # homeassistant/components/nmbs/sensor.py
    from __future__ import annotations

    from datetime import datetime, timedelta # Add timedelta import
    import logging
    # ... other imports

    _LOGGER = logging.getLogger(__name__)

    # Define an appropriate polling interval
    SCAN_INTERVAL = timedelta(minutes=1)

    DEFAULT_NAME = "NMBS"
    # ... rest of the file
    ```

2.  **Rationale for the suggestion:**
    *   **Explicitly Sets Interval:** This directly addresses the rule's requirement to *set* an interval.
    *   **Appropriateness:** A 60-second interval is often a good default for transport data. It reduces the polling frequency by half compared to the HA default of 30 seconds, which is beneficial for the external API, especially if users configure multiple NMBS sensors.
    *   **User Flexibility:** Users who require more frequent updates can still override this using the [global custom polling interval feature](https://www.home-assistant.io/common-tasks/general/#defining-a-custom-polling-interval).

By implementing this change, the `nmbs` integration will make a conscious decision about its polling behavior, aligning with the `appropriate-polling` quality scale rule.

_Created at 2025-05-11 07:18:46. Prompt tokens: 10216, Output tokens: 1053, Total tokens: 15023_
