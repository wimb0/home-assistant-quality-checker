# wled: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **done**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `log-when-unavailable` rule requires that an integration logs a message once when a device or service it depends on becomes unavailable, and once again when it becomes available. This logging should ideally be at the `INFO` level. The `DataUpdateCoordinator` in Home Assistant provides built-in support for this: if `_async_update_data` raises `UpdateFailed`, the coordinator logs a `WARNING` when the connection is first lost and an `INFO` message when it's recovered.

The `wled` integration utilizes two `DataUpdateCoordinator` instances:
1.  `WLEDDataUpdateCoordinator`: Manages fetching data from the WLED device itself.
2.  `WLEDReleasesDataUpdateCoordinator`: Manages fetching WLED firmware release information from GitHub.

**Analysis of `WLEDDataUpdateCoordinator` (`coordinator.py`):**
*   In the `_async_update_data` method, which is used for polling the WLED device, communication errors with the device (raising `WLEDError` from the `wled` library) are caught and re-raised as `UpdateFailed`. This correctly triggers the `DataUpdateCoordinator`'s built-in logging for unavailability and recovery.
    ```python
    # coordinator.py
    async def _async_update_data(self) -> WLEDDevice:
        """Fetch data from WLED."""
        try:
            device = await self.wled.update()
        except WLEDError as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error
        # ...
        return device
    ```
*   The coordinator also implements a WebSocket connection for real-time updates. In the `listen` method within `_use_websocket`, WebSocket connection errors (`WLEDConnectionClosedError`, `WLEDError`) are handled:
    ```python
    # coordinator.py
    except WLEDConnectionClosedError as err:
        self.last_update_success = False # Signals unavailability to the coordinator
        self.logger.info(err) # Logs specific WebSocket error
    except WLEDError as err:
        self.last_update_success = False # Signals unavailability
        self.async_update_listeners()
        self.logger.error(err) # Logs specific WebSocket error
    ```
    When a WebSocket error occurs, `self.last_update_success` is set to `False`. This makes entities unavailable. The integration also logs a specific `INFO` or `ERROR` message about the WebSocket issue. If data is subsequently successfully received (either via polling fallback or WebSocket reconnection calling `self.async_set_updated_data`), the `DataUpdateCoordinator`'s logic will log an `INFO` message indicating recovery because `last_update_success` transitions from `False` to `True`.

**Analysis of `WLEDReleasesDataUpdateCoordinator` (`coordinator.py`):**
*   Similarly, in its `_async_update_data` method, errors from fetching release data from GitHub (raising `WLEDError`) are caught and re-raised as `UpdateFailed`.
    ```python
    # coordinator.py
    async def _async_update_data(self) -> Releases:
        """Fetch release data from WLED."""
        try:
            return await self.wled.releases()
        except WLEDError as error:
            raise UpdateFailed(f"Invalid response from GitHub API: {error}") from error
    ```
    This again correctly uses the `DataUpdateCoordinator`'s mechanism for logging unavailability and recovery of the GitHub data source.

**Conclusion:**
The `wled` integration correctly implements the `log-when-unavailable` rule by leveraging the `DataUpdateCoordinator`.
*   For polling updates, raising `UpdateFailed` ensures the coordinator logs unavailability (as `WARNING`) and recovery (as `INFO`).
*   For WebSocket updates, specific errors are logged by the integration, and `last_update_success` is set to `False`. Recovery is then logged by the coordinator as `INFO`.

This ensures that users are informed when the WLED device (or the GitHub releases source) becomes unavailable and when it's back online, with logs generated once per state transition. While the initial unavailability log from the coordinator is a `WARNING` rather than `INFO` as strictly suggested by the rule, this is the standard behavior of `DataUpdateCoordinator` and is consistent with the rule's example for coordinator-based integrations. The core requirement of logging these state changes is met.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:55:48. Prompt tokens: 22506, Output tokens: 1120, Total tokens: 28158_
