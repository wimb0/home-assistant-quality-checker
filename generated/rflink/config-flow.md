# rflink: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [rflink](https://www.home-assistant.io/integrations/rflink/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule requires integrations to be configurable through the Home Assistant user interface. This enhances user experience by providing a consistent setup process.

The `rflink` integration currently **does not** follow this rule. It relies on YAML configuration for its setup.

Evidence:

1.  **`manifest.json`**:
    The `manifest.json` file for `rflink` does not include the `"config_flow": true` entry, which is necessary to indicate UI-based configuration support.
    ```json
    // homeassistant/components/rflink/manifest.json
    {
      "domain": "rflink",
      "name": "RFLink",
      "codeowners": ["@javicalle"],
      "documentation": "https://www.home-assistant.io/integrations/rflink",
      "iot_class": "assumed_state",
      "loggers": ["rflink"],
      "quality_scale": "legacy", // Often indicates older integrations without config flow
      "requirements": ["rflink==0.0.66"]
    }
    ```

2.  **No `config_flow.py`**:
    There is no `config_flow.py` file within the `homeassistant/components/rflink/` directory. This file is essential for implementing the UI setup logic.

3.  **YAML Configuration (`CONFIG_SCHEMA`)**:
    The integration's `__init__.py` defines a `CONFIG_SCHEMA`, indicating that it expects its primary configuration (like port, host, and other settings) to be provided in `configuration.yaml`.
    ```python
    // homeassistant/components/rflink/__init__.py
    CONFIG_SCHEMA = vol.Schema(
        {
            DOMAIN: vol.Schema(
                {
                    vol.Required(CONF_PORT): vol.Any(cv.port, cv.string),
                    vol.Optional(CONF_HOST): cv.string,
                    vol.Optional(CONF_WAIT_FOR_ACK, default=True): cv.boolean,
                    # ... other YAML configured options
                }
            )
        },
        extra=vol.ALLOW_EXTRA,
    )

    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        # ... uses config[DOMAIN] ...
    ```
    This `async_setup` function processes the YAML configuration. For a config flow-based integration, `async_setup_entry` would be used instead, processing a `ConfigEntry`.

4.  **`strings.json`**:
    The `strings.json` file lacks a `config` section, which is required to provide text for the config flow UI (titles, descriptions, field labels, error messages). It currently only contains service descriptions.
    ```json
    // homeassistant/components/rflink/strings.json
    {
      "services": {
        // ... service definitions ...
      }
      // Missing "config": { ... } section
    }
    ```

5.  **Platform YAML Configuration**:
    Individual platforms like `light`, `switch`, `sensor`, `cover`, and `binary_sensor` also use `PLATFORM_SCHEMA` to define devices and their settings in YAML. Migrating to config flow would also involve rethinking how these platform-specific configurations are handled, typically moving towards discovery or options flows for entity customization.

    Example from `homeassistant/components/rflink/light.py`:
    ```python
    PLATFORM_SCHEMA = LIGHT_PLATFORM_SCHEMA.extend(
        {
            vol.Optional(
                CONF_DEVICE_DEFAULTS, default=DEVICE_DEFAULTS_SCHEMA({})
            ): DEVICE_DEFAULTS_SCHEMA,
            vol.Optional(CONF_AUTOMATIC_ADD, default=True): cv.boolean,
            vol.Optional(CONF_DEVICES, default={}): {
                cv.string: vol.Schema(
                    # ... device specific config from YAML ...
                )
            },
        },
        extra=vol.ALLOW_EXTRA,
    )
    ```

The rule applies to `rflink` as it is not listed as an exception in ADR-0010. Therefore, it needs to be updated to support UI-based configuration.

## Suggestions

To make the `rflink` integration compliant with the `config-flow` rule, the following steps are recommended:

1.  **Update `manifest.json`**:
    Add `"config_flow": true` to `homeassistant/components/rflink/manifest.json`.
    ```json
    {
      "domain": "rflink",
      "name": "RFLink",
      // ... other entries ...
      "config_flow": true,
      "iot_class": "assumed_state",
      // ...
    }
    ```

2.  **Create `config_flow.py`**:
    Create a new file `homeassistant/components/rflink/config_flow.py`. This file will contain the logic for the configuration flow.

    A basic structure could be:
    ```python
    # homeassistant/components/rflink/config_flow.py
    import voluptuous as vol
    from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
    from homeassistant.const import CONF_HOST, CONF_PORT
    from homeassistant.core import callback # Ensure this import for OptionsFlow
    # Potentially import a function to test connection to RFLink gateway

    from .const import DOMAIN # Assuming DOMAIN is defined in .const

    # Schema for user input during the config flow
    # Distinguish between serial and TCP setup or combine them intelligently
    # For simplicity, a combined initial approach:
    DATA_SCHEMA = vol.Schema({
        vol.Required(CONF_PORT): str, # Can be serial device path or TCP port
        vol.Optional(CONF_HOST): str, # If provided, implies TCP
    })

    class RflinkConfigFlow(ConfigFlow, domain=DOMAIN):
        """Handle a config flow for RFLink."""
        VERSION = 1

        async def async_step_user(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            """Handle the initial step."""
            errors: dict[str, str] = {}
            if user_input is not None:
                # TODO: Add logic to test the connection to the RFLink device
                # using user_input[CONF_PORT] and user_input.get(CONF_HOST).
                # If connection fails, set errors["base"] = "cannot_connect"
                # and show the form again.
                # Example:
                # try:
                #     await self.hass.async_add_executor_job(
                #         test_rflink_connection, user_input[CONF_PORT], user_input.get(CONF_HOST)
                #     )
                # except CannotConnect:
                #     errors["base"] = "cannot_connect"
                # except Exception: # pylint: disable=broad-except
                #     errors["base"] = "unknown" # Or a more specific error

                if not errors:
                    # Title for the config entry, can be dynamic (e.g., based on host/port)
                    title = f"RFLink {user_input.get(CONF_HOST, '')}:{user_input[CONF_PORT]}"
                    if not user_input.get(CONF_HOST): # Serial connection
                        title = f"RFLink {user_input[CONF_PORT]}"

                    return self.async_create_entry(title=title, data=user_input)

            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA, errors=errors
            )
    ```

3.  **Update `strings.json`**:
    Add a `config` section to `homeassistant/components/rflink/strings.json` for UI text.
    ```json
    {
      "config": {
        "step": {
          "user": {
            "title": "Set up RFLink Gateway",
            "description": "Enter connection details for your RFLink gateway. For serial connections, provide the device path (e.g., /dev/ttyUSB0 or COM3) in 'Port' and leave 'Host' empty. For TCP connections, specify both 'Host' and 'Port'.",
            "data": {
              "port": "Port (Serial Device Path or TCP Port)",
              "host": "Host (Optional, for TCP connection)"
            }
          }
        },
        "error": {
          "cannot_connect": "Failed to connect to the RFLink gateway. Please check your settings and ensure the gateway is accessible.",
          "unknown": "An unknown error occurred."
        },
        "abort": {
          "already_configured": "RFLink gateway is already configured."
        }
      },
      "options": { // For options flow (see suggestion 5)
        "step": {
          "init": {
            "title": "RFLink Options",
            "data": {
              "wait_for_ack": "Wait for command acknowledgement from RFLink gateway",
              "reconnect_interval": "Reconnect interval (seconds)",
              "tcp_keepalive_idle_timer": "TCP Keepalive Idle Timer (seconds, 0 to disable, TCP only)",
              "ignore_devices": "Ignored Device IDs (comma-separated list)"
            }
          }
        }
      },
      "services": {
        // ... existing service strings ...
      }
    }
    ```

4.  **Refactor `__init__.py`**:
    *   Remove `CONFIG_SCHEMA`.
    *   Replace `async_setup` with `async_setup_entry` and `async_unload_entry`.
    *   `async_setup_entry` will receive a `ConfigEntry` object. Connection parameters (`port`, `host`) will be in `entry.data`. Other settings (like `wait_for_ack`, `reconnect_interval`, `ignore_devices`) should come from `entry.options` if an options flow is implemented.
    *   The logic for establishing the connection, setting up listeners, and registering services will move into `async_setup_entry`.
    *   Use `hass.config_entries.async_setup_platforms(entry, PLATFORMS)` to load entities from different platforms (light, switch, etc.).

    Example snippet for `__init__.py`:
    ```python
    # homeassistant/components/rflink/__init__.py
    # Remove CONFIG_SCHEMA

    # Define PLATFORMS if not already defined, e.g.
    # from homeassistant.const import Platform
    # PLATFORMS = [Platform.LIGHT, Platform.SWITCH, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.COVER]


    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Set up RFLink from a config entry."""
        port = entry.data[CONF_PORT]
        host = entry.data.get(CONF_HOST) # Optional

        # Retrieve options with defaults
        wait_for_ack = entry.options.get(CONF_WAIT_FOR_ACK, True)
        reconnect_interval = entry.options.get(CONF_RECONNECT_INTERVAL, DEFAULT_RECONNECT_INTERVAL)
        # ... and other options

        # ... (Connection logic from current async_setup, adapted to use entry.data/options) ...
        # Example:
        # connection_params = {
        #     "port": port,
        #     "host": host,
        #     "event_callback": event_callback_from_config_entry,
        #     "disconnect_callback": reconnect_from_config_entry,
        #     "ignore": entry.options.get(CONF_IGNORE_DEVICES, []),
        #     # ...
        # }
        # Store the RFLink protocol instance or transport on hass.data[DOMAIN][entry.entry_id] for access

        # Load platforms
        await hass.config_entries.async_setup_platforms(entry, PLATFORMS)

        # Register an update listener for options
        entry.async_on_unload(entry.add_update_listener(update_listener))

        return True

    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Unload a config entry."""
        # Close connection, remove listeners, etc.
        # Unload platforms
        return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
        """Handle options update."""
        # This is called when options are changed.
        # Typically, you might need to reconfigure the connection or certain aspects.
        # A simple way is to reload the entry.
        await hass.config_entries.async_reload(entry.entry_id)
    ```

5.  **Implement an Options Flow (Recommended)**:
    For settings like `wait_for_ack`, `reconnect_interval`, `tcp_keepalive_idle_timer`, and `ignore_devices`, implement an options flow handler in `config_flow.py`. This allows users to change these settings via the UI after the initial setup.
    *   The `ConfigFlow` class would need a static method:
        ```python
        @staticmethod
        @callback
        def async_get_options_flow(config_entry):
            return RflinkOptionsFlowHandler(config_entry)
        ```
    *   Define `RflinkOptionsFlowHandler`:
        ```python
        # In config_flow.py
        from homeassistant.config_entries import OptionsFlow, ConfigEntry
        from homeassistant.core import callback

        # Define constants for options if not already defined
        CONF_WAIT_FOR_ACK = "wait_for_ack"
        CONF_RECONNECT_INTERVAL = "reconnect_interval"
        CONF_TCP_KEEPALIVE_IDLE = "tcp_keepalive_idle_timer" # as in __init__.py
        CONF_IGNORE_DEVICES = "ignore_devices"

        class RflinkOptionsFlowHandler(OptionsFlow):
            def __init__(self, config_entry: ConfigEntry):
                self.config_entry = config_entry

            async def async_step_init(self, user_input=None):
                if user_input is not None:
                    # Convert comma-separated string for ignore_devices to list
                    if isinstance(user_input.get(CONF_IGNORE_DEVICES), str):
                        user_input[CONF_IGNORE_DEVICES] = [
                            item.strip() for item in user_input[CONF_IGNORE_DEVICES].split(",") if item.strip()
                        ]
                    else:
                         user_input[CONF_IGNORE_DEVICES] = []

                    return self.async_create_entry(title="", data=user_input)

                # Default values for options form from current settings
                # Convert ignore_devices list back to comma-separated string for display
                current_ignore_devices = self.config_entry.options.get(CONF_IGNORE_DEVICES, [])
                ignore_devices_str = ", ".join(current_ignore_devices)

                options_schema = vol.Schema({
                    vol.Optional(
                        CONF_WAIT_FOR_ACK,
                        default=self.config_entry.options.get(CONF_WAIT_FOR_ACK, True)
                    ): bool,
                    vol.Optional(
                        CONF_RECONNECT_INTERVAL,
                        default=self.config_entry.options.get(CONF_RECONNECT_INTERVAL, 10) # Use const DEFAULT_RECONNECT_INTERVAL
                    ): int,
                    vol.Optional(
                        CONF_TCP_KEEPALIVE_IDLE,
                        default=self.config_entry.options.get(CONF_TCP_KEEPALIVE_IDLE, 3600) # Use const DEFAULT_TCP_KEEPALIVE_IDLE_TIMER
                    ): int,
                    vol.Optional(
                        CONF_IGNORE_DEVICES,
                        default=ignore_devices_str
                    ): str,
                })
                return self.async_show_form(step_id="init", data_schema=options_schema)
        ```

6.  **Adapt Platform Setup**:
    Each platform (`light.py`, `sensor.py`, etc.) will need an `async_setup_entry` function instead of `async_setup_platform`. This function will receive the `ConfigEntry` and the `async_add_entities` callback. The logic for discovering or setting up entities will be based on the main RFLink connection established by the central `async_setup_entry`. YAML configuration for devices (`CONF_DEVICES` in platform schemas) would be removed. Device discovery or alternative UI configuration methods would be needed for these.

These changes are significant but will bring the `rflink` integration in line with current Home Assistant standards for user configuration.

_Created at 2025-05-28 13:26:32. Prompt tokens: 18034, Output tokens: 3967, Total tokens: 26538_
