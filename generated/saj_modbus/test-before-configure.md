# saj_modbus: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **todo**                                                                     |

## Overview

The `test-before-configure` rule requires integrations that connect to a device or service to validate the connection during the configuration flow, before the entry is created. This provides immediate feedback to the user if the provided details (like IP address or port) are incorrect.

This rule applies to the `saj_modbus` integration as it connects to an inverter over the local network, which requires a correct host and port.

The integration currently does not follow this rule. In `config_flow.py`, the `async_step_user` method only performs basic input validation, such as checking if the host is already configured or if the host string is in a valid format. It does not attempt to establish a connection with the inverter to verify the provided host and port.

```python
# homeassistant/components/saj_modbus/config_flow.py

# ...
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]

            if self._host_in_configuration_exists(host):
                errors[CONF_HOST] = "already_configured"
            elif not host_valid(user_input[CONF_HOST]):
                errors[CONF_HOST] = "Invalid host IP"
            else:
                # No connection test is performed here.
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
# ...
```

If a user enters an incorrect IP address or port, the integration will be set up but will fail to connect later, leading to a poor user experience.

## Suggestions

To comply with this rule, you should add a connection test to the `async_step_user` method in `config_flow.py`. This involves creating a temporary client, attempting to communicate with the device, and handling any potential connection errors.

1.  **Update `strings.json`**: Add new error keys for connection failures.

    ```json
    // homeassistant/components/saj_modbus/strings.json
    {
      "config": {
        "step": {
          ...
        },
        "error": {
          "already_configured": "Device is already configured",
          "cannot_connect": "Failed to connect to the inverter. Please check the host and port.",
          "unknown": "An unknown error occurred."
        },
        "abort": {
          "already_configured": "Device is already configured"
        }
      },
      ...
    }
    ```

2.  **Modify `config_flow.py`**: Import necessary components and implement the connection test logic.

    ```python
    # homeassistant/components/saj_modbus/config_flow.py

    import ipaddress
    import re
    from typing import Any
    import voluptuous as vol
    import logging

    from homeassistant.config_entries import (
        ConfigEntry,
        ConfigFlow,
        FlowResult,
        OptionsFlow,
    )
    from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
    from homeassistant.core import HomeAssistant, callback
    from pymodbus.exceptions import ConnectionException

    from .const import DEFAULT_NAME, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN
    from .hub import SAJModbusHub

    _LOGGER = logging.getLogger(__name__)

    # ... (rest of the file remains the same until async_step_user)

    class SAJModbusConfigFlow(ConfigFlow, domain=DOMAIN):
        """SAJ Modbus configflow."""

        VERSION = 2

        def _host_in_configuration_exists(self, host) -> bool:
            """Return True if host exists in configuration."""
            if host in saj_modbus_entries(self.hass):
                return True
            return False

        async def async_step_user(
            self, user_input: dict[str, Any] | None = None
        ) -> FlowResult:
            """Handle the initial step."""
            errors = {}

            if user_input is not None:
                host = user_input[CONF_HOST]

                if self._host_in_configuration_exists(host):
                    errors[CONF_HOST] = "already_configured"
                elif not host_valid(user_input[CONF_HOST]):
                    errors[CONF_HOST] = "Invalid host IP"
                else:
                    hub = SAJModbusHub(
                        self.hass,
                        name=user_input.get(CONF_NAME),
                        host=host,
                        port=user_input.get(CONF_PORT),
                        scan_interval=user_input.get(CONF_SCAN_INTERVAL),
                    )
                    try:
                        # Attempt to read inverter data to verify the connection
                        inverter_data = await self.hass.async_add_executor_job(
                            hub.read_modbus_inverter_data
                        )
                        if not inverter_data:
                            # This occurs if read_modbus_inverter_data returns {} on Modbus error
                            errors["base"] = "cannot_connect"
                        else:
                            await self.async_set_unique_id(user_input[CONF_HOST])
                            self._abort_if_unique_id_configured()
                            return self.async_create_entry(
                                title=user_input[CONF_NAME], data=user_input
                            )
                    except ConnectionException:
                        _LOGGER.warning("Could not connect to SAJ inverter at %s", host)
                        errors["base"] = "cannot_connect"
                    except Exception:  # noqa: BLE001
                        _LOGGER.exception("Unexpected exception during connection test")
                        errors["base"] = "unknown"
                    finally:
                        # Ensure the client connection is closed after the test
                        await self.hass.async_add_executor_job(hub.close)

            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA, errors=errors
            )

        # ... (rest of the file)
    ```

These changes will use the `SAJModbusHub` to perform a test read from the inverter. If the connection fails (either due to a network issue caught by `ConnectionException` or a Modbus error handled inside `read_modbus_inverter_data`), an error message will be displayed to the user, preventing the creation of a non-functional configuration entry.

---

_Created at 2025-06-11 21:35:19. Prompt tokens: 16879, Output tokens: 1694, Total tokens: 21854._

_AI can be wrong. Always verify the report and the code against the rule._
