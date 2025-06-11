# saj_modbus: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **todo**                                                                 |

## Overview

The `unique-config-entry` rule applies to this integration as it uses a config flow to set up a network-based device, and a user could inadvertently try to configure the same inverter multiple times.

The integration currently attempts to follow this rule by using the host/IP address as a unique identifier. This is implemented in `config_flow.py`:

```python
# homeassistant/components/saj_modbus/config_flow.py:68-74
            if self._host_in_configuration_exists(host):
                errors[CONF_HOST] = "already_configured"
            elif not host_valid(user_input[CONF_HOST]):
                errors[CONF_HOST] = "Invalid host IP"
            else:
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
```

While this prevents adding the exact same host twice, it is not a robust solution. The host IP address can change (e.g., if assigned by DHCP). If the inverter's IP address changes, a user could add it again, leading to a duplicate device in Home Assistant, which is exactly what this rule aims to prevent.

The best practice, as demonstrated in the rule's documentation, is to connect to the device during the configuration flow and retrieve a stable hardware identifier, such as a serial number. The `saj_modbus` integration is capable of fetching the inverter's serial number, as seen in `hub.py`:

```python
# homeassistant/components/saj_modbus/hub.py:149
"sn": ''.join(chr(registers[i] >> 8) + chr(registers[i] & 0xFF) for i in range(3, 13)).rstrip('\x00'),
```

Because the integration does not use this stable serial number as the config entry's unique ID, it does not fully comply with the rule's intent, as duplicate device entries are still possible.

## Suggestions

To fully comply with this rule, the config flow should be updated to fetch the inverter's serial number and use it as the unique ID for the config entry. This ensures that the device itself is identified uniquely, regardless of its IP address.

This also provides a better user experience by validating the connection to the inverter before the configuration entry is created, which aligns with the `test-before-configure` rule.

Here is a recommended approach for modifying `async_step_user` in `config_flow.py`:

1.  **Import necessary components:** You will need to import `SAJModbusHub` and relevant exception classes.
2.  **Connect to the device:** In `async_step_user`, after receiving user input, create a temporary instance of the `SAJModbusHub`.
3.  **Fetch the serial number:** Use the hub instance to connect to the inverter and call `read_modbus_inverter_data` to get the device's serial number (`sn`). This I/O operation should be run in an executor.
4.  **Set the unique ID:** Use the fetched serial number as the unique ID for the config entry using `await self.async_set_unique_id(serial_number)`.
5.  **Handle errors:** Wrap the connection and data fetching logic in a `try...except` block to catch connection errors (e.g., `pymodbus.exceptions.ConnectionException`) and show appropriate errors to the user (e.g., `cannot_connect`).

**Example implementation:**

```python
# In homeassistant/components/saj_modbus/config_flow.py

from pymodbus.exceptions import ConnectionException
from .hub import SAJModbusHub
# ... other imports

class SAJModbusConfigFlow(ConfigFlow, domain=DOMAIN):
    """SAJ Modbus configflow."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            if not host_valid(user_input[CONF_HOST]):
                errors[CONF_HOST] = "Invalid host IP"
            else:
                hub = SAJModbusHub(
                    self.hass,
                    name=user_input[CONF_NAME],
                    host=user_input[CONF_HOST],
                    port=user_input[CONF_PORT],
                    scan_interval=user_input[CONF_SCAN_INTERVAL],
                )
                try:
                    # Fetch inverter data to get the serial number
                    inverter_data = await self.hass.async_add_executor_job(
                        hub.read_modbus_inverter_data
                    )
                    serial_number = inverter_data.get("sn")

                    if not serial_number:
                        # Could connect, but didn't get a serial number
                        errors["base"] = "cannot_retrieve_sn" # Add to strings.json
                    else:
                        await self.async_set_unique_id(serial_number)
                        # This will abort if the SN is already configured.
                        # It can also be used to update the host if the IP has changed.
                        self._abort_if_unique_id_configured(updates=user_input)

                        return self.async_create_entry(
                            title=user_input[CONF_NAME], data=user_input
                        )

                except ConnectionException:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                finally:
                    # Ensure the temporary connection is closed
                    await self.hass.async_add_executor_job(hub.close)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
```

---

_Created at 2025-06-11 21:37:00. Prompt tokens: 17296, Output tokens: 1462, Total tokens: 22749._

_AI can be wrong. Always verify the report and the code against the rule._
