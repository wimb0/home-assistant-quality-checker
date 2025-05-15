# open_epaper_link: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `log-when-unavailable` rule applies to the `open_epaper_link` integration. This integration acts as a hub (`integration_type: hub`) communicating with an OpenEPaperLink Access Point (AP) via a WebSocket connection. The AP is a service/device that can become unavailable due to network issues, AP reboots, or other errors. The rule requires that the integration logs a message at `INFO` level once when the AP becomes unavailable and once when the connection is restored.

Currently, the `open_epaper_link` integration does **not** fully follow this rule.

1.  **Logging Level:**
    *   When the WebSocket connection to the AP fails (e.g., `aiohttp.ClientError` or other exceptions during connection attempts in `hub.py`'s `_websocket_handler`), messages are logged at `ERROR` level (e.g., `_LOGGER.error("WebSocket connection error: %s", err)`). The rule requires `INFO` level.
    *   When the AP signals it is rebooting (via an "errMsg":"REBOOTING" WebSocket message), a message is logged at `DEBUG` level (`_LOGGER.debug("AP is rebooting")` in `_handle_message` within `hub.py`). This should be an `INFO` level message indicating unavailability.
    *   When the WebSocket connection is re-established after a period of unavailability, a message is logged at `DEBUG` level (`_LOGGER.debug("Connected to websocket at %s", ws_url)` in `_websocket_handler`). The rule requires an `INFO` level message indicating the connection is back online.
    *   The initial successful connection is logged at `INFO` level by `async_start_websocket` (`_LOGGER.info("WebSocket connection established successfully")`), which is good for the very first connection.

2.  **Log Once Mechanism:**
    *   The integration lacks a stateful flag (similar to `_had_logged_unavailable` in `DataUpdateCoordinator`) within the `Hub` class in `hub.py` to ensure that "unavailable" and "back online" messages are logged only once per state change.
    *   For example, if reconnection attempts fail repeatedly, the `_LOGGER.error` messages for connection failures in `_websocket_handler` will be logged on each attempt, potentially spamming the logs. The rule requires logging unavailability only once for that period of downtime.

Specifically, the `Hub._websocket_handler` method in `homeassistant/components/open_epaper_link/hub.py` is responsible for managing the WebSocket connection. Its current logging for connection state changes does not align with the rule's requirements for level and frequency.

## Suggestions

To make the `open_epaper_link` integration compliant with the `log-when-unavailable` rule, the following changes are recommended in `homeassistant/components/open_epaper_link/hub.py`:

1.  **Introduce a State Flag:**
    Add a boolean instance variable to the `Hub` class to track whether the "unavailable" state has been logged.
    ```python
    # In class Hub:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        # ... existing initializations ...
        self.online = False
        self._connection_unavailable_logged: bool = False # New flag
    ```

2.  **Modify Logging in `_websocket_handler`:**
    Update the `_websocket_handler` method to use this flag and log messages at the `INFO` level.

    *   **When connection is successfully established:**
        ```python
        # Inside _websocket_handler's try block, after ws_connect succeeds:
        # async with self._session.ws_connect(ws_url, heartbeat=30) as ws:
            if not self.online: # If we were previously marked as offline
                if self._connection_unavailable_logged:
                    _LOGGER.info("Connection to OpenEPaperLink AP at %s restored.", self.host)
                    self._connection_unavailable_logged = False
                # else:
                # The very first successful connection log is handled by async_start_websocket
                # or can be moved here:
                # _LOGGER.info("Successfully connected to OpenEPaperLink AP at %s.", self.host)

            self.online = True
            async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", True)
            _LOGGER.debug("WebSocket session established with %s", ws_url) # Existing debug log is fine for verbose details
            # ... rest of the message handling loop ...
        ```
        The `async_start_websocket` method already logs `_LOGGER.info("WebSocket connection established successfully")` for the *initial* connection. This can be kept, or all "connected" logging consolidated into `_websocket_handler`. If kept, the `else` block for initial connection logging in `_websocket_handler` might not be needed if `_connection_unavailable_logged` is `False` initially.

    *   **When connection fails or is lost:**
        This includes `aiohttp.ClientError`, other exceptions during `ws_connect`, or issues within the message receiving loop that lead to disconnection.
        ```python
        # Inside _websocket_handler's except blocks for connection errors (e.g., aiohttp.ClientError, websockets.exceptions.WebSocketException, asyncio.TimeoutError, OSError):
        # except (aiohttp.ClientError, websockets.exceptions.WebSocketException, asyncio.TimeoutError, OSError) as err:
            if self.online: # If it was previously online and now transitioning to offline
                _LOGGER.info("Connection to OpenEPaperLink AP at %s lost: %s. Will attempt to reconnect.", self.host, err)
                self._connection_unavailable_logged = True
            elif not self._connection_unavailable_logged: # If it was already offline (e.g., initial connect failed) and we haven't logged it yet
                _LOGGER.info("Failed to connect to OpenEPaperLink AP at %s: %s. Will attempt to reconnect.", self.host, err)
                self._connection_unavailable_logged = True
            
            self.online = False
            async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", False)
            # _LOGGER.error(...) calls for these specific errors should be removed or changed if this INFO log covers them.
        ```

    *   **When AP signals "REBOOTING" in `_handle_message`:**
        ```python
        # Inside _handle_message, when "errMsg" in data and data["errMsg"] == "REBOOTING":
            _LOGGER.debug("AP is rebooting") # Keep this debug log for specifics
            if self.online and not self._connection_unavailable_logged:
                _LOGGER.info("OpenEPaperLink AP at %s is rebooting, connection will be lost. Will attempt to reconnect.", self.host)
                self._connection_unavailable_logged = True
            
            self._ap_data["ap_state"] = "Offline" # Or similar status update
            self.online = False
            async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", False)
            # ... existing logic to cancel WebSocket and schedule reconnection ...
        ```

3.  **Review Initial Connection Logging in `async_start_websocket`:**
    Ensure that the logging in `async_start_websocket` complements the new logging in `_websocket_handler`.
    *   The line `_LOGGER.info("WebSocket connection established successfully")` is good for the very first successful connection.
    *   The line `_LOGGER.error("Failed to establish WebSocket connection")` if initial connection times out should be changed. If `_websocket_handler` has already logged an `INFO` level "Failed to connect..." message because `_connection_unavailable_logged` was `False`, this `ERROR` log is redundant and at the wrong level. It might be better to rely on `_websocket_handler`'s logging.

**Why these changes satisfy the rule:**
*   **Log Level:** All primary "unavailable" and "back online" messages will be at `INFO` level.
*   **Log Once:** The `_connection_unavailable_logged` flag ensures that messages for a continuous period of unavailability, or for the transition back to available, are logged only once.
*   **Clarity:** The suggested log messages are more descriptive of the state change (e.g., "Connection lost", "Connection restored", "Failed to connect").

_Created at 2025-05-14 20:51:54. Prompt tokens: 60780, Output tokens: 2031, Total tokens: 71619_
