```markdown
# pegel_online: async-dependency

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [async-dependency](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/async-dependency)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that any external dependency used by the integration for network or I/O operations should be an asynchronous library. Home Assistant is built on `asyncio`, and using asynchronous dependencies avoids performance-costly context switches between the event loop and other threads. The `async-dependency` rule is closely related to the `inject-websession` rule, as an async dependency should typically accept and use the Home Assistant-provided `aiohttp` client session.

The `pegel_online` integration uses the `aiopegelonline` library, as specified in its `manifest.json`: `"requirements": ["aiopegelonline==0.1.1"]`. The name `aiopegelonline` clearly indicates that it is an asynchronous library, following the common convention of prefixing async Python libraries with `aio`.

Upon reviewing the code, the integration correctly interacts with this library using `await` calls:

*   In `__init__.py`, the initialization fetches station details asynchronously: `station = await api.async_get_station_details(station_uuid)`.
*   In `coordinator.py`, the data update fetches measurements asynchronously: `return await self.api.async_get_station_measurements(self.station.uuid)` within the `_async_update_data` method.
*   In `config_flow.py`, the search for nearby stations is asynchronous: `stations = await api.async_get_nearby_stations(...)`.

Furthermore, the integration correctly follows the related `inject-websession` rule by passing the Home Assistant `aiohttp` client session to the library constructor in both `__init__.py` and `config_flow.py`: `PegelOnline(async_get_clientsession(hass))`. This confirms that the dependency utilizes the Home Assistant-managed async HTTP client for its network operations.

Therefore, the `pegel_online` integration fully complies with the `async-dependency` rule.

## Suggestions

No suggestions needed. The integration correctly uses an asynchronous dependency and interacts with it appropriately.
```

_Created at 2025-05-25 11:26:22. Prompt tokens: 5582, Output tokens: 557, Total tokens: 6772_
