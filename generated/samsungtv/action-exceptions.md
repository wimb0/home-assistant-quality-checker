```markdown
# samsungtv: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that integration service actions raise appropriate exceptions (`HomeAssistantError` for internal/device errors, `ServiceValidationError` for incorrect user input) when they encounter failures.

The `samsungtv` integration exposes several service actions via the `media_player` and `remote` platforms (e.g., turning on/off, volume control, sending keys, selecting source, playing media).

The integration partially follows this rule:
*   Some methods, like `MediaPlayerEntity.async_set_volume_level`, correctly catch specific errors (`UpnpActionResponseError`) and re-raise them as `HomeAssistantError`.
*   Some methods, like `MediaPlayerEntity.async_turn_on` (for a specific misconfiguration case), `MediaPlayerEntity.async_play_media` (partially), and `MediaPlayerEntity.async_select_source`, raise `HomeAssistantError` for scenarios related to configuration or invalid input. While `HomeAssistantError` is acceptable, `ServiceValidationError` might be more appropriate for input validation failures (`async_play_media`, `async_select_source`).
*   However, a significant number of service actions rely on the `SamsungTVBridge.async_send_keys` method (which is called by entity methods like `SamsungTVEntity._async_send_keys` and `SamsungTVBridge._async_send_power_off`). The underlying bridge methods (`_send_key` for legacy, `_async_send_commands` for websocket) often catch communication-related exceptions (e.g., `OSError`, `ConnectionClosed`, `WebSocketException`, `ConnectionFailure`, `AsyncioTimeoutError`) and either log them, ignore them, or only handle specific cases (like re-authentication). This prevents the failures from being consistently propagated as `HomeAssistantError` exceptions to the calling service actions, meaning the user interface may not indicate that a command failed due to a communication issue.

Specifically, service calls triggering methods like:
*   `MediaPlayerEntity.async_turn_off` (via `_bridge.async_power_off` -> `_async_send_power_off` -> `async_send_keys`)
*   `MediaPlayerEntity.async_volume_up`/`async_volume_down`/`async_mute_volume` (via `_async_send_keys` -> `_bridge.async_send_keys`)
*   `MediaPlayerEntity.async_media_*` (via `_async_send_keys` -> `_bridge.async_send_keys`)
*   `MediaPlayerEntity.async_play_media` (via `_async_launch_app` -> `_async_send_commands` or `_async_send_keys` -> `_bridge.async_send_keys`)
*   `RemoteEntity.async_send_command` (via `_bridge.async_send_keys`)

may fail silently or log errors instead of raising exceptions that indicate failure to the user.

## Suggestions

To comply with the `action-exceptions` rule, the following areas should be addressed:

1.  **Propagate Communication Errors:** Modify the `SamsungTVBridge.async_send_keys` method to catch relevant exceptions raised by its internal implementation (`_send_key` for legacy, `_async_send_commands` for websocket) and re-raise them consistently as `HomeAssistantError`. The internal methods should only catch exceptions they handle (like connection retries or specific device responses) but allow underlying connection/communication errors to bubble up or return a status indicating failure.

    *   **Example (Conceptual):**
        ```python
        # In samsungtv/bridge.py

        async def async_send_keys(self, keys: list[str]) -> None:
            """Send a list of keys to the tv."""
            try:
                if isinstance(self, SamsungTVLegacyBridge):
                    first_key = True
                    for key in keys:
                        if first_key:
                            first_key = False
                        else:
                            await asyncio.sleep(KEY_PRESS_TIMEOUT)
                        await self.hass.async_add_executor_job(self._send_key, key)
                elif isinstance(self, SamsungTVWSBaseBridge): # Covers WS and Encrypted
                    commands = [SendRemoteKey.click(key) for key in keys] # Or SendEncryptedRemoteKey
                    await self._async_send_commands(commands) # This needs to allow errors to bubble up
                else:
                    # Handle unsupported bridge type or raise error
                    pass # Or raise HomeAssistantError("Unsupported bridge type")

            # Catch exceptions that _send_key or _async_send_commands allow through
            # and were not handled internally by the bridge's methods.
            except (ConnectionError, TimeoutError, OSError, WebSocketException, ConnectionFailure, # etc.
                    UnhandledResponse, AccessDenied) as err: # Catch specific known library errors
                LOGGER.error("Failed to send command to %s: %s", self.host, err)
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="error_sending_command", # Ensure this translation key exists or use inline message
                    translation_placeholders={"error": repr(err), "host": self.host},
                ) from err

        # Ensure _send_key and _async_send_commands handle internal retries/specific
        # device responses but re-raise unexpected or unrecoverable communication errors.
        # Example: In _send_key, remove the `except OSError: pass` block.
        ```

2.  **Refine Input Validation Exceptions:** For service actions that fail due to incorrect user input or configuration (like specifying an unknown source or an invalid channel format), consider raising `ServiceValidationError` instead of `HomeAssistantError`.

    *   **Example:**
        ```python
        # In homeassistant/components/samsungtv/media_player.py

        async def async_select_source(self, source: str) -> None:
            """Select input source."""
            if self._app_list and source in self._app_list:
                await self._async_launch_app(self._app_list[source])
                return

            if source in SOURCES:
                await self._async_send_keys([SOURCES[source]])
                return

            # Change to ServiceValidationError
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="source_unsupported", # Ensure this translation key exists or use inline message
                translation_placeholders={"entity": self.entity_id, "source": source},
            )
        ```
        Similar changes can be made to `async_play_media` for invalid channel format validation and potentially to the `async_turn_on` fallback error.

3.  **Enhance UPnP Exception Handling:** In `MediaPlayerEntity.async_set_volume_level`, expand the exception handling to catch a broader range of `UpnpError` types (e.g., `UpnpCommunicationError`, `UpnpResponseError`, `UpnpConnectionError`) and re-raise them as `HomeAssistantError`, as these also indicate failures in the action itself due to communication issues with the device.

By implementing these suggestions, the integration will provide more informative feedback to the user when service actions fail, improving the user experience and aiding in troubleshooting.
```

_Created at 2025-05-25 11:29:38. Prompt tokens: 30127, Output tokens: 1722, Total tokens: 34874_
