# stiebel_eltron: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-configure` rule requires integrations to test the connection to a device or service during the config flow. If the connection fails, an appropriate error message should be displayed to the user, preventing setup with invalid parameters.

This rule applies to the `stiebel_eltron` integration because it connects to a physical device (Stiebel Eltron heat pump via Modbus TCP) and uses a config flow for setup. It is not a helper integration, nor does it rely solely on runtime discovery for initial setup, as it requires host and port information from the user.

The `stiebel_eltron` integration correctly implements this rule in its config flow:

1.  **User-initiated setup (`async_step_user`):**
    In `homeassistant/components/stiebel_eltron/config_flow.py`, the `async_step_user` method handles user input for `host` and `port`.
    ```python
    # homeassistant/components/stiebel_eltron/config_flow.py
    # ...
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            # ...
            client = StiebelEltronAPI(
                ModbusTcpClient(user_input[CONF_HOST], port=user_input[CONF_PORT]), 1
            )
            try:
                success = await self.hass.async_add_executor_job(client.update) # Connection test
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown" # Error for unexpected issues
            else:
                if not success:
                    errors["base"] = "cannot_connect" # Error for connection failure
            if not errors:
                return self.async_create_entry(title="Stiebel Eltron", data=user_input)

        return self.async_show_form( # Shows form again with errors if any
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )
    ```
    - It initializes the `StiebelEltronAPI` client with the provided host and port.
    - It then calls `await self.hass.async_add_executor_job(client.update)`. The `client.update()` method is expected to perform the actual connection attempt and data retrieval.
    - If `client.update()` returns `False` (indicating a failure to connect or retrieve initial data), `errors["base"]` is set to `"cannot_connect"`.
    - If any other `Exception` occurs during this process, `errors["base"]` is set to `"unknown"`.
    - If `errors` is populated, `self.async_show_form` is called again, passing the `errors` dictionary. This redisplays the form with the relevant error message to the user, as defined in `strings.json` (`"cannot_connect"` or `"unknown"`).
    - The entry is only created if `errors` remains empty, signifying a successful connection test.

2.  **Import-initiated setup (`async_step_import`):**
    The `async_step_import` method, used for YAML configuration import, also performs a similar connection test:
    ```python
    # homeassistant/components/stiebel_eltron/config_flow.py
    # ...
    async def async_step_import(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        # ...
        client = StiebelEltronAPI(
            ModbusTcpClient(user_input[CONF_HOST], port=user_input[CONF_PORT]), 1
        )
        try:
            success = await self.hass.async_add_executor_job(client.update) # Connection test
        except Exception:
            _LOGGER.exception("Unexpected exception")
            return self.async_abort(reason="unknown") # Aborts flow on unexpected error

        if not success:
            return self.async_abort(reason="cannot_connect") # Aborts flow on connection failure

        return self.async_create_entry(
            # ...
        )
    ```
    - It performs the same `client.update()` call.
    - If `client.update()` returns `False` or an exception occurs, the flow is aborted with an appropriate reason (`"cannot_connect"` or `"unknown"`). This prevents the creation of a non-functional config entry from an invalid YAML import. The `__init__.py` file then uses these reasons to create an issue in the issue registry, informing the user about the failed import.

The error messages `"cannot_connect"` and `"unknown"` are defined in `homeassistant/components/stiebel_eltron/strings.json`, ensuring user-friendly feedback.

Therefore, the integration effectively tests the connection before completing the configuration and provides feedback to the user in case of failure, fully adhering to the `test-before-configure` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 14:59:10. Prompt tokens: 6321, Output tokens: 1306, Total tokens: 9106_
