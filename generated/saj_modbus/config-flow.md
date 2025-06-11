# saj_modbus: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **todo**                                                                 |

## Overview

The `saj_modbus` integration is a device integration and therefore the `config-flow` rule applies. The integration has a config flow, as indicated by `"config_flow": true` in `manifest.json` and the presence of a `config_flow.py` file.

However, the implementation does not fully follow the rule's requirements and best practices, leading to a `todo` status. The following issues were identified:

1.  **Incorrect Data vs. Options Handling:** The rule states that settings not needed for the initial connection should be stored in `ConfigEntry.options`. In `config_flow.py`, `scan_interval` is collected during the initial user step but is stored in `ConfigEntry.data` along with connection-specific details (`host`, `port`).
    ```python
    # config_flow.py
    return self.async_create_entry(
        title=user_input[CONF_NAME], data=user_input
    )
    ```
    Conversely, `__init__.py` attempts to read `scan_interval` from `entry.options`.
    ```python
    # __init__.py
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    ```
    This mismatch means the `scan_interval` value provided by the user during initial setup is ignored, and the default is used instead until the user re-configures it via the options flow.

2.  **Improper `strings.json` Structure:** The rule emphasizes a user-friendly experience, which includes using `data_description` in `strings.json` to provide context for input fields. The integration's `strings.json` file incorrectly places descriptive help text in the `data` value, which is meant for the field label. The `data_description` key is missing entirely.
    ```json
    // strings.json
    "data": {
      "host": "The ip-address of your SAJ Inverter modbus device",
      "name": "The prefix to be used for your SAJ Inverter sensors",
      // ...
    }
    ```

3.  **Remnants of YAML Configuration:** `__init__.py` still contains a `CONFIG_SCHEMA`. While it appears unused by the `async_setup` function, its presence implies support for YAML configuration, which goes against the principle of having a single, UI-based setup method for integrations with a config flow. To be fully compliant, all YAML configuration methods for setting up the integration should be removed.

## Suggestions

To make the `saj_modbus` integration compliant with the `config-flow` rule, the following changes are recommended:

1.  **Separate `data` and `options` on Creation:**
    Modify the `async_step_user` method in `config_flow.py` to separate connection-critical information (`data`) from user-configurable settings (`options`) when creating the config entry.

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
                # This should be a translation key, not a raw string.
                errors[CONF_HOST] = "invalid_host" 
            else:
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                
                # Suggested Change: Separate data and options
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                    options={
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )
    # ...
    ```

2.  **Correct the `strings.json` file:**
    Restructure `strings.json` to use `data` for short, concise labels and `data_description` for the helpful context text.

    ```json
    // homeassistant/components/saj_modbus/strings.json
    {
      "config": {
        "step": {
          "user": {
            "title": "Define your SAJ Inverter modbus-connection",
            "data": {
              "host": "IP Address or Hostname",
              "name": "Name",
              "port": "Port",
              "scan_interval": "Scan Interval"
            },
            "data_description": {
              "host": "The IP address or hostname of your SAJ Inverter modbus device.",
              "name": "The name to use as a prefix for your SAJ Inverter sensors.",
              "port": "The TCP port on which to connect to the SAJ Inverter.",
              "scan_interval": "The polling frequency of the modbus registers in seconds."
            }
          }
        },
        "error": {
          "already_configured": "Device is already configured",
          "invalid_host": "The host is not a valid IP address or hostname."
        },
        "abort": {
          "already_configured": "Device is already configured"
        }
      },
      "options": {
        "step": {
          "init": {
            "data": {
              "scan_interval": "Scan Interval"
            },
            "data_description": {
              "scan_interval": "The polling frequency of the modbus registers in seconds."
            }
          }
        }
      },
      "services": {
        // ...
      }
    }
    ```
    *Note: An `options` section was also added to `strings.json` for the options flow, which is a best practice.*

3.  **Remove Legacy YAML Configuration Code:**
    To fully embrace the UI-driven configuration, remove the unused `CONFIG_SCHEMA` from `__init__.py`. The `async_setup` function can also be removed as it becomes redundant; `hass.data.setdefault(DOMAIN, {})` in `async_setup_entry` is sufficient.

    ```python
    # homeassistant/components/saj_modbus/__init__.py

    # REMOVE THESE LINES
    # SAJ_MODBUS_SCHEMA = vol.Schema(...)
    # CONFIG_SCHEMA = vol.Schema(...)

    # REMOVE THIS FUNCTION
    # async def async_setup(hass, config):
    #    """Set up the SAJ modbus component."""
    #    hass.data[DOMAIN] = {}
    #    return True

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
        """Set up a SAJ mobus."""
        # This line already handles the initialization previously done by async_setup
        hass.data.setdefault(DOMAIN, {})
        # ... rest of the function
    ```

---

_Created at 2025-06-11 21:32:04. Prompt tokens: 16963, Output tokens: 1779, Total tokens: 22049._

_AI can be wrong. Always verify the report and the code against the rule._
