```markdown
# pegel_online: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires polling integrations to set an appropriate polling interval based on the nature of the data being fetched to avoid excessive requests. The `pegel_online` integration is a cloud-polling integration, as indicated by its `iot_class` in the `manifest.json`, meaning this rule applies.

The integration uses a `DataUpdateCoordinator` to manage fetching data, which is the recommended approach for polling integrations. The `PegelOnlineDataUpdateCoordinator` class, defined in `homeassistant/components/pegel_online/coordinator.py`, initializes the coordinator with an `update_interval`.

Specifically, the constructor `PegelOnlineDataUpdateCoordinator.__init__` sets the interval using `update_interval=MIN_TIME_BETWEEN_UPDATES`. Looking at `homeassistant/components/pegel_online/const.py`, `MIN_TIME_BETWEEN_UPDATES` is defined as `timedelta(minutes=5)`.

A 5-minute polling interval seems appropriate for this integration, which retrieves water level, flow, and temperature data from official measuring stations. While not real-time, this data doesn't typically change every few seconds, making a 5-minute interval a reasonable balance between data freshness and minimizing requests to the external service. This aligns with the spirit of the rule, which suggests intervals should reflect the typical update frequency of the data.

The integration correctly implements the rule by using the `update_interval` parameter of the `DataUpdateCoordinator`.

## Suggestions

No suggestions needed. The integration follows the rule.
```

_Created at 2025-05-25 11:21:51. Prompt tokens: 6049, Output tokens: 449, Total tokens: 7418_
