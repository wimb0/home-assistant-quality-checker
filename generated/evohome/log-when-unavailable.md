# evohome: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The rule `log-when-unavailable` requires that an integration logs a message at `INFO` level when a connected device or service becomes unavailable, and logs another `INFO` message when it becomes available again. Crucially, the "unavailable" message should only be logged once for a continuous period of unavailability to avoid spamming logs.

The `evohome` integration uses `EvoDataUpdateCoordinator`, a subclass of `DataUpdateCoordinator`, to manage polling data from the cloud service.

**Applicability:**
This rule applies to `evohome` as it is a cloud-polling integration that can experience periods of unavailability due to network issues, API rate limits, or service outages.

**Current Behavior & Compliance:**
1.  **Raising `UpdateFailed`**: The `EvoDataUpdateCoordinator` (specifically in its `_update_v2_api_state` method within `coordinator.py`) correctly identifies failures (e.g., `evohomeasync2.ApiRequestFailedError`, `evohomeasync2.EvohomeError`) and raises `UpdateFailed`. This is the standard practice for integrations using `DataUpdateCoordinator`.

2.  **`DataUpdateCoordinator` Logging**:
    *   **On Unavailability**: When `UpdateFailed` is raised, the base `DataUpdateCoordinator` logs an `ERROR` message (e.g., `"Error fetching [coordinator_name] data: [exception_details]"`). This occurs if a previous successful refresh had happened and a scheduled refresh was active.
    *   **On Recovery**: When a subsequent update succeeds after failures, `DataUpdateCoordinator` logs an `INFO` message (e.g., `"Data fetching resumed"`). This part correctly meets the rule's requirement for an `INFO` level log upon recovery and is logged once per recovery.

**Gap Analysis:**
The `evohome` integration, by relying on the default `DataUpdateCoordinator` logging, does not fully meet the `log-when-unavailable` rule due to two main points concerning the "unavailable" event:
1.  **Log Level**: The rule specifies that the "unavailable" log should be at `INFO` level. However, `DataUpdateCoordinator` logs this event at `ERROR` level.
    ```python
    # homeassistant/helpers/update_coordinator.py DataUpdateCoordinator._async_handle_update_failure
    if self._unsub_refresh:  # Did we have a successful refresh before?
        self.logger.error("Error fetching %s data: %s", self.name, exc) # Logs at ERROR
    ```
2.  **Log Once**: The rule states, "Be sure to log only once in total to avoid spamming the logs" for the period of unavailability. The `DataUpdateCoordinator`, when an `update_interval` is configured (as it is for `evohome`), will re-attempt updates on schedule. If these attempts continue to fail, the `logger.error` message mentioned above will be logged on *each* failed scheduled attempt. This constitutes log spamming for the same ongoing unavailability issue. The rule's example for non-coordinator entities uses a boolean flag (e.g., `_unavailable_logged`) to prevent this, a mechanism not present by default in `DataUpdateCoordinator` for its error log.

Therefore, while the integration correctly signals failures to the coordinator and logs recovery appropriately, its handling of the initial and ongoing unavailability logs does not align with the rule's specific requirements for log level and frequency.

## Suggestions

To make the `evohome` integration compliant with the `log-when-unavailable` rule, the `EvoDataUpdateCoordinator` should take direct responsibility for logging the "unavailable" message at `INFO` level and ensuring it's logged only once per continuous unavailability period.

1.  **Add a Flag**: Introduce a boolean instance variable to `EvoDataUpdateCoordinator` to track if the "unavailable" message has been logged for the current unavailability period.
    ```python
    # homeassistant/components/evohome/coordinator.py
    class EvoDataUpdateCoordinator(DataUpdateCoordinator):
        def __init__(self, ...):
            super().__init__(...)
            self._integration_unavailable_logged: bool = False
            # ... other initializations
    ```

2.  **Modify `_update_v2_api_state`**: This method is the primary point where API communication happens and failures are detected. Update it to log at `INFO` level upon the first detection of unavailability and set the flag. Reset the flag upon successful communication.

    ```python
    # homeassistant/components/evohome/coordinator.py
    class EvoDataUpdateCoordinator(DataUpdateCoordinator):
        # ... (init as above) ...

        async def _update_v2_api_state(self, *args: Any) -> None:
            """Get the latest modes, temperatures, setpoints of a Location."""
            try:
                status = await self.loc.update()
                # If successful and unavailable was previously logged by this integration, reset flag.
                # The DataUpdateCoordinator will handle the "Data fetching resumed" INFO log.
                if self._integration_unavailable_logged:
                    self._integration_unavailable_logged = False
                self.logger.debug("Status = %s", status)

            except ec2.ApiRequestFailedError as err:
                err_msg = str(err)
                if err.status == HTTPStatus.TOO_MANY_REQUESTS:
                    err_msg = (
                        "The vendor's API rate limit has been exceeded. "
                        f"Consider increasing the {CONF_SCAN_INTERVAL}." # CONF_SCAN_INTERVAL is available via self.config_entry.options
                    )
                
                if not self._integration_unavailable_logged:
                    self.logger.info("Evohome service unavailable: %s", err_msg)
                    self._integration_unavailable_logged = True
                raise UpdateFailed(err_msg) from err # Still raise UpdateFailed for coordinator state management

            except ec2.EvohomeError as err: # Catch other evohome specific errors
                err_msg = str(err)
                if not self._integration_unavailable_logged:
                    self.logger.info("Evohome service encountered an error: %s", err_msg)
                    self._integration_unavailable_logged = True
                raise UpdateFailed(err_msg) from err # Still raise UpdateFailed
    ```

**Explanation of Suggested Changes:**

*   `self._integration_unavailable_logged`: This flag ensures that the custom `INFO` log for unavailability is emitted only once when the service first becomes unavailable.
*   **Custom `INFO` Log**: When an `ec2.ApiRequestFailedError` or `ec2.EvohomeError` occurs, if `_integration_unavailable_logged` is `False`, an `INFO` level log message is emitted by the integration itself, and the flag is set to `True`.
*   **Raising `UpdateFailed`**: `UpdateFailed` is still raised after the custom log. This is crucial for `DataUpdateCoordinator` to:
    *   Correctly manage its internal state (`last_update_success`).
    *   Update entity availability.
    *   Log its "Data fetching resumed" `INFO` message when the connection is re-established.
*   **Resetting the Flag**: When `self.loc.update()` is successful, `_integration_unavailable_logged` is reset to `False`. This prepares it for the next potential unavailability period.

This approach ensures:
*   The "unavailable" event is logged at `INFO` level by the integration.
*   This `INFO` log occurs only once per continuous unavailability period.
*   The "available again" event is logged at `INFO` level by the `DataUpdateCoordinator` (as it currently does).
*   The standard `DataUpdateCoordinator` mechanisms for state and entity availability updates remain functional.

While this won't stop `DataUpdateCoordinator` from logging its own `ERROR` messages on repeated failures (which is a characteristic of `DataUpdateCoordinator` itself), the integration will have fulfilled its obligation to provide the "unavailable" log as specified by the rule (INFO level, once).

---

_Created at 2025-05-29 12:46:45. Prompt tokens: 22121, Output tokens: 1918, Total tokens: 35031._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
