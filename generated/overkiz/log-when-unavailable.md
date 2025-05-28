# overkiz: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `log-when-unavailable` rule requires integrations to log a message when a device or service becomes unavailable and another message when it becomes available again. These logs should ideally be at the `INFO` level and occur only once per state change to avoid log spamming.

The `overkiz` integration utilizes a `DataUpdateCoordinator` (`OverkizDataUpdateCoordinator`) for managing data updates from the Overkiz platform. This is relevant because the rule provides specific guidance for coordinator-based integrations:

> "The coordinator has the logic for logging once built in. The only thing that you need to do in the coordinator is to raise `UpdateFailed` when the device or service is unavailable."

The `OverkizDataUpdateCoordinator`'s `_async_update_data` method (in `coordinator.py`) handles communication with the Overkiz API. It includes error handling for various scenarios that would indicate service unavailability:

```python
# homeassistant/components/overkiz/coordinator.py
    async def _async_update_data(self) -> dict[str, Device]:
        """Fetch Overkiz data via event listener."""
        try:
            events = await self.client.fetch_events()
        # ... (auth exceptions leading to ConfigEntryAuthFailed) ...
        except TooManyConcurrentRequestsException as exception:
            raise UpdateFailed("Too many concurrent requests.") from exception
        except TooManyRequestsException as exception:
            raise UpdateFailed("Too many requests, try again later.") from exception
        except MaintenanceException as exception:
            raise UpdateFailed("Server is down for maintenance.") from exception
        except InvalidEventListenerIdException as exception:
            raise UpdateFailed(exception) from exception
        except (TimeoutError, ClientConnectorError) as exception: # ClientConnectorError includes aiohttp.ClientOSError
            raise UpdateFailed("Failed to connect.") from exception
        # ... (logic for ServerDisconnectedError with relogin attempt, which may also raise UpdateFailed) ...
```

When these specific exceptions (e.g., `TooManyConcurrentRequestsException`, `TimeoutError`, `ClientConnectorError`, `MaintenanceException`) are caught, the `OverkizDataUpdateCoordinator` correctly raises an `UpdateFailed` exception with a descriptive message.

The base `DataUpdateCoordinator` in Home Assistant core, which `OverkizDataUpdateCoordinator` inherits from, has built-in logic to handle these `UpdateFailed` exceptions:
1.  On the first `UpdateFailed` occurrence after a successful update, it logs an error message using the logger provided by the integration (e.g., `self.logger.error("Error fetching %s data: %s", self.name, err)`).
2.  When the update subsequently succeeds after a failure, it logs an informational message (e.g., `self.logger.info("Previously failed %s update recovered", self.name)`).

This behavior fulfills the "log once when unavailable and once when back connected" requirement. The `overkiz` integration passes its `LOGGER` (from `overkiz.const`) to its `OverkizDataUpdateCoordinator`, which is then used by the base `DataUpdateCoordinator` for these logs.

While the rule states that "Logging should happen at `info` level" for both unavailability and recovery, the standard `DataUpdateCoordinator` logs the initial unavailability at `ERROR` level and recovery at `INFO` level. Given that the rule's example for coordinator-based integrations *only* requires raising `UpdateFailed`, and explicitly mentions the coordinator's built-in logging, the existing `ERROR` (for unavailability) and `INFO` (for recovery) logging pattern provided by the core `DataUpdateCoordinator` is considered compliant with the rule's intent for this type of integration.

Failures during the initial setup (`async_setup_entry` in `__init__.py`) raise `ConfigEntryNotReady` or `ConfigEntryAuthFailed`. These are handled and logged by Home Assistant's core config entry system, which is appropriate for setup-time issues and slightly different from the ongoing unavailability during updates that this rule primarily targets.

Therefore, the `overkiz` integration correctly follows the prescribed pattern for coordinator-based integrations by raising `UpdateFailed` when the service is determined to be unavailable, allowing the `DataUpdateCoordinator` to manage the logging.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:22:33. Prompt tokens: 87291, Output tokens: 1061, Total tokens: 95714_
