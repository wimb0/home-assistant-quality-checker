```markdown
# pegel_online: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires integrations to log when they become unavailable due to connectivity issues with a device or service, and again when they become available, ensuring this logging happens only once per state change to avoid spamming logs.

The `pegel_online` integration utilizes the `DataUpdateCoordinator` pattern, which includes built-in logic for handling availability and logging.

In `homeassistant/components/pegel_online/coordinator.py`, the `PegelOnlineDataUpdateCoordinator._async_update_data` method is responsible for fetching data from the API. This method correctly catches connection errors (`CONNECT_ERRORS`) and raises `UpdateFailed`:

```python
    async def _async_update_data(self) -> StationMeasurements:
        """Fetch data from API endpoint."""
        try:
            return await self.api.async_get_station_measurements(self.station.uuid)
        except CONNECT_ERRORS as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"error": str(err)},
            ) from err
```

When a `DataUpdateCoordinator`'s `_async_update_data` method raises `UpdateFailed`, the coordinator automatically marks the associated entities as unavailable. Crucially, the `DataUpdateCoordinator` implementation within Home Assistant's core includes the necessary logic to log:
1.  When the update fails (indicating unavailability) - logged at `ERROR` level, but only once until a successful update occurs.
2.  When a subsequent update succeeds after a failure (indicating recovery) - logged at `INFO` level, only once after being unavailable.

Although the rule text mentions logging at the `info` level for both states, the example implementation provided for coordinators only shows raising `UpdateFailed`. The standard behavior of the `DataUpdateCoordinator` when `UpdateFailed` is raised is to log at `ERROR` for the failure and `INFO` for the recovery, both logged only once per state change. By correctly using `DataUpdateCoordinator` and raising `UpdateFailed`, the `pegel_online` integration leverages this built-in mechanism, satisfying the core requirement of logging once when unavailable and once when available again.

The `config_flow.py` also handles `CONNECT_ERRORS` during setup (`async_step_user`), but this correctly results in a UI error message rather than logging, which is appropriate for the initial configuration process.

Thus, the integration follows the rule by implementing the recommended coordinator pattern which handles the required logging behavior.

## Suggestions

No suggestions needed. The integration correctly implements the recommended pattern using `DataUpdateCoordinator`.
```

_Created at 2025-05-25 11:23:44. Prompt tokens: 6187, Output tokens: 697, Total tokens: 7763_
