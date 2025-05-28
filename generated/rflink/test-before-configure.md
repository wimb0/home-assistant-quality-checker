# rflink: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [rflink](https://www.home-assistant.io/integrations/rflink/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **todo**                                                                 |

## Overview

The `test-before-configure` rule requires that integrations test the connection to a device or service within the config flow before finalizing the configuration. This is to provide immediate feedback to the user if connection parameters (like IP address, port, credentials, or serial port) are incorrect, or if the device is unreachable.

This rule applies to the `rflink` integration because it connects to an RFLink gateway, which can be either a serial device or a network device (TCP). Issues such as an incorrect serial port, wrong IP address/port for a TCP connection, or firewall problems can prevent the integration from working.

The `rflink` integration currently does **NOT** follow this rule.
1.  **No Config Flow:** The integration is configured exclusively via `configuration.yaml`, as indicated by the absence of a `config_flow.py` file and `config_flow: true` in its `manifest.json`. The rule explicitly states the test should occur "in the config flow."
2.  **Behavior During Setup:** In `__init__.py`, the `async_setup` function initiates a connection attempt in a background task (`hass.async_create_task(connect(), eager_start=False)`). If this initial connection fails (e.g., due to `SerialException`, `OSError`, or `TimeoutError` within the `connect` coroutine), an error is logged, and a reconnection is scheduled. However, the `async_setup` function itself returns `True`, allowing Home Assistant to load the integration as if setup were successful. The user is not directly informed via the UI at setup time that the provided connection parameters are invalid; they would need to check logs or observe that entities are unavailable or not working.

To comply with the rule, `rflink` would need to implement a config flow and perform the connection test within it, showing an error to the user in the UI if the test fails.

## Suggestions

To make the `rflink` integration compliant with the `test-before-configure` rule, the following steps are recommended:

1.  **Implement a Config Flow:**
    *   Create a `config_flow.py` file for the `rflink` integration.
    *   Add `config_flow: true` to the `manifest.json`.
    *   The config flow should handle both serial and network (TCP) connections. This might involve a menu step (`async_step_user` offering "Serial" or "Network") or separate initial steps.

2.  **Test Connection in the Config Flow:**
    *   In the appropriate step of the config flow (e.g., `async_step_user` or a subsequent step after collecting port/host details), attempt to establish a connection to the RFLink gateway.
    *   The connection logic currently in `__init__.py`'s `connect` function can be adapted for this purpose. Specifically, the call to `create_rflink_connection` and the subsequent attempt to establish the connection (`await connection`).

    **Example (Conceptual for TCP connection):**
    ```python
    # homeassistant/components/rflink/config_flow.py
    import asyncio
    from rflink.protocol import create_rflink_connection
    from serial import SerialException
    import voluptuous as vol

    from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
    from homeassistant.const import CONF_HOST, CONF_PORT
    from homeassistant.core import HomeAssistant

    from .const import DOMAIN # Assuming DOMAIN is defined in .const

    # Define your data schema (example for TCP)
    DATA_SCHEMA_TCP = vol.Schema({
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): int,
    })

    async def test_rflink_connection(hass: HomeAssistant, host: str | None, port: any) -> bool:
        """Test the RFLink connection."""
        # This is a simplified version of the connection logic.
        # You'll need to adapt the logic from __init__.py's connect()
        # including timeout handling.
        # create_rflink_connection might need to be made async or run in executor
        # if it's blocking. The rflink library itself uses asyncio, so it should integrate.

        connection_coro = create_rflink_connection(
            port=port,
            host=host,
            loop=hass.loop,
            # Other parameters like ignore, keepalive might be needed or configured later
        )
        try:
            async with asyncio.timeout(10): # Use a reasonable timeout
                transport, protocol = await connection_coro
                # It's good practice to close the test connection if successful and not needed immediately
                if transport:
                    transport.close()
                return True
        except (SerialException, OSError, TimeoutError, ConnectionRefusedError):
            # Catch specific exceptions related to connection failure
            return False
        except Exception: # Catch any other unexpected error during test
            # Log this unexpected error
            return False


    class RflinkConfigFlow(ConfigFlow, domain=DOMAIN):
        VERSION = 1

        async def async_step_user(self, user_input=None) -> ConfigFlowResult:
            """Handle the initial step."""
            # This could be a menu to choose between serial and TCP
            # For simplicity, let's assume TCP for this example
            return await self.async_step_tcp()

        async def async_step_tcp(self, user_input=None) -> ConfigFlowResult:
            errors: dict[str, str] = {}
            if user_input is not None:
                try:
                    # Use hass.async_add_executor_job if test_rflink_connection
                    # contains blocking I/O not compatible with asyncio,
                    # or ensure create_rflink_connection and its usage are fully async.
                    # The rflink library seems to be asyncio-native.
                    if await test_rflink_connection(
                        self.hass, user_input[CONF_HOST], user_input[CONF_PORT]
                    ):
                        return self.async_create_entry(
                            title=f"RFLink ({user_input[CONF_HOST]}:{user_input[CONF_PORT]})",
                            data=user_input,
                        )
                    errors["base"] = "cannot_connect"
                except Exception:  # noqa: BLE001
                    # _LOGGER.exception("Unexpected exception") # Add logging
                    errors["base"] = "unknown"

            return self.async_show_form(
                step_id="tcp", data_schema=DATA_SCHEMA_TCP, errors=errors
            )

        # You would also need a similar async_step_serial for serial connections
    ```

3.  **Provide User Feedback:**
    *   If the connection test fails, return `self.async_show_form` with an appropriate error key in the `errors` dictionary (e.g., `errors["base"] = "cannot_connect"` or more specific errors like `errors[CONF_PORT] = "invalid_port"`). This will display an error message to the user in the UI.
    *   Only if the connection test is successful, proceed to call `self.async_create_entry` to create the config entry.

By implementing these changes, the `rflink` integration will:
*   Allow users to configure it via the UI.
*   Test the provided connection parameters *before* the configuration is saved.
*   Provide immediate feedback if the connection cannot be established, guiding the user to correct their input.
This directly addresses the requirements of the `test-before-configure` rule.

_Created at 2025-05-28 13:32:40. Prompt tokens: 17950, Output tokens: 1808, Total tokens: 22167_
