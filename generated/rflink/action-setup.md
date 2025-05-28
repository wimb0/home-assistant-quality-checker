# rflink: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [rflink](https://www.home-assistant.io/integrations/rflink/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `action-setup` rule requires that service actions are registered in the `async_setup` function and that they properly validate their state and input, raising `ServiceValidationError` when appropriate. This ensures services are discoverable and provide meaningful feedback to the user, especially if underlying requirements (like a loaded config entry or an active connection) are not met.

The `rflink` integration registers one service, `send_command`, in its `async_setup` function, which aligns with the first part of the rule.

However, the integration does not fully follow the rule's requirements regarding error handling and validation within the service call handler:

1.  **Connection State Check**: The `async_send_command` service handler in `homeassistant/components/rflink/__init__.py` does not explicitly check if the RFLink gateway connection is active before attempting to send a command.
    *   The connection status is managed via `RflinkCommand._protocol`, which is set upon successful connection and cleared if the connection is lost.
    *   If `RflinkCommand._protocol` is `None` (i.e., not connected), calling `await RflinkCommand.send_command(...)` will lead to an `AttributeError` when `cls._protocol.send_command_ack` is accessed. This results in an unhandled exception trace in the logs rather than a user-friendly `ServiceValidationError`.
    *   The rule emphasizes that if a service depends on a "loaded" state (analogous to an active connection for `rflink`), this should be checked, and `ServiceValidationError` raised if not met.

2.  **Command Execution Failure**: If `RflinkCommand.send_command(...)` returns `False` (which can happen if the RFLink device does not acknowledge the command when `wait_for_ack` is enabled, or if there's a send failure at the protocol level), the current implementation in `async_send_command` only logs an error:
    ```python
    if not (
        await RflinkCommand.send_command(
            call.data.get(CONF_DEVICE_ID), call.data.get(CONF_COMMAND)
        )
    ):
        _LOGGER.error("Failed Rflink command for %s", str(call.data))
    ```
    This does not raise a `ServiceValidationError`, so the user is not informed through the service call response that the command failed.

3.  **Library-Specific Exceptions**: The `RflinkCommand.send_command` method (which calls the `rflink` library) can raise exceptions like `CommandInvalid` from the `rflink` library if the provided `device_id` or `command` parameters are malformed. These exceptions are not currently caught and re-raised as `ServiceValidationError` by the `async_send_command` service handler.

Due to these gaps in error handling and user feedback via `ServiceValidationError`, the integration does not fully comply with the `action-setup` rule.

## Suggestions

To make the `rflink` integration compliant with the `action-setup` rule, the `async_send_command` service handler in `homeassistant/components/rflink/__init__.py` should be updated as follows:

1.  **Import necessary exceptions**:
    ```python
    from rflink.exceptions import CommandInvalid
    from homeassistant.exceptions import ServiceValidationError
    ```

2.  **Modify the `async_send_command` function**:
    ```python
    async def async_send_command(call: ServiceCall) -> None:
        """Send Rflink command."""
        _LOGGER.debug("Rflink command for %s", str(call.data))

        # 1. Check if RFLink connection is active
        if not RflinkCommand.is_connected():
            raise ServiceValidationError(
                "RFLink connection is not active. Cannot send command."
            )

        device_id = call.data.get(CONF_DEVICE_ID)
        command_action = call.data.get(CONF_COMMAND) # Renamed to avoid potential confusion

        try:
            # 2. Attempt to send the command and handle return status
            success = await RflinkCommand.send_command(device_id, command_action)
            if not success:
                # This typically means ACK was not received or a lower-level send failed
                raise ServiceValidationError(
                    f"Failed to send RFLink command to device '{device_id}' with action '{command_action}'. "
                    "The command may not have been acknowledged or a send error occurred."
                )
            
            _LOGGER.info(
                "Successfully sent RFLink command to device '%s', action '%s'",
                device_id,
                command_action,
            )
            # Propagate event for internal listeners (e.g., entity state updates)
            async_dispatcher_send(
                hass,
                SIGNAL_EVENT,
                {
                    EVENT_KEY_ID: device_id,
                    EVENT_KEY_COMMAND: command_action,
                },
            )
        except CommandInvalid as err:
            # 3. Handle specific invalid command errors from the rflink library
            _LOGGER.error(
                "Invalid RFLink command for device '%s', action '%s': %s",
                device_id,
                command_action,
                err,
            )
            raise ServiceValidationError(
                f"Invalid RFLink command format for device '{device_id}', action '{command_action}': {err}"
            ) from err
        except AttributeError as err: 
            # Catch potential AttributeError if _protocol becomes None unexpectedly
            _LOGGER.error("RFLink internal error during send_command: %s", err)
            raise ServiceValidationError(
                "RFLink internal error: Protocol became unavailable unexpectedly while sending command."
            ) from err
        except Exception as err: # Catch-all for other unexpected errors
            _LOGGER.error(
                "Unexpected error sending RFLink command to device '%s', action '%s': %s",
                device_id,
                command_action,
                err,
            )
            raise ServiceValidationError(
                f"An unexpected error occurred while sending RFLink command to device '{device_id}', action '{command_action}': {err}"
            ) from err
    ```

**Why these changes satisfy the rule:**

*   **Connection Check**: Adding `if not RflinkCommand.is_connected(): raise ServiceValidationError(...)` ensures that if the fundamental requirement for the service (an active RFLink connection) is not met, the user receives immediate and clear feedback. This is analogous to checking `entry.state is not ConfigEntryState.LOADED` for config entry-based integrations.
*   **Command Failure Feedback**: Changing the `if not success:` block to `raise ServiceValidationError(...)` ensures that failures in command execution (like no acknowledgment) are reported back to the user, rather than just being logged silently from the service's perspective.
*   **Library Exception Handling**: Catching `CommandInvalid` (and potentially other specific exceptions from the `rflink` library) and re-raising them as `ServiceValidationError` provides more granular error messages to the user if their input leads to a malformed command at the RFLink protocol level.

These changes will make the `send_command` service more robust and user-friendly, aligning with the intent of the `action-setup` quality scale rule.

_Created at 2025-05-28 13:23:32. Prompt tokens: 17858, Output tokens: 1751, Total tokens: 26110_
