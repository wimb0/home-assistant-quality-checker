# adax: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `test-before-configure` rule requires that integrations implementing a config flow test the connection to the device or service before creating the configuration entry. This is to provide immediate feedback to the user about potential issues like incorrect credentials, network problems, or device unavailability.

The `adax` integration supports two connection types: "Cloud" and "Local", both configured through its config flow.

**Applicability:**
This rule applies to the `adax` integration because:
1.  It uses a config flow (`config_flow: true` in `manifest.json`).
2.  It connects to external devices (Adax heaters) and a cloud service, making connection testing relevant and beneficial for user experience.
3.  It is not a helper integration and does not solely rely on runtime auto-discovery for its setup.

**Assessment:**
The `adax` integration **fully follows** this rule for both its local and cloud configuration paths.

**1. Local Connection (`async_step_local` in `config_flow.py`):**
   - The user provides Wi-Fi SSID and password.
   - The flow then attempts to configure the device using `await configurator.configure_device()`. This call inherently tests the ability to connect to and configure the heater.
   - Specific failures during this process are handled by `try...except` blocks:
     ```python
     try:
         device_configured = await configurator.configure_device()
     except adax_local.HeaterNotAvailable:
         return self.async_abort(reason="heater_not_available")
     except adax_local.HeaterNotFound:
         return self.async_abort(reason="heater_not_found")
     except adax_local.InvalidWifiCred:
         return self.async_abort(reason="invalid_auth")
     ```
     These `async_abort` calls prevent the entry creation and inform the user of specific issues like invalid Wi-Fi credentials or the heater not being found/available.
   - If `configure_device()` returns `False` (indicating a general failure to configure/connect not caught by specific exceptions), an error is shown on the form:
     ```python
     if not device_configured:
         return self.async_show_form(
             step_id="local",
             data_schema=data_schema,
             errors={"base": "cannot_connect"},
         )
     ```
     This allows the user to retry or correct input if applicable.
   - Only if `device_configured` is `True` does the flow proceed to `self.async_create_entry(...)`.

**2. Cloud Connection (`async_step_cloud` in `config_flow.py`):**
   - The user provides an Account ID and Password.
   - The flow attempts to retrieve an authentication token using `await adax.get_adax_token(...)`. This call tests connectivity to the Adax cloud service and the validity of the provided credentials.
   - If `get_adax_token()` returns `None` (indicating failed authentication or connection), an error is shown on the form:
     ```python
     token = await adax.get_adax_token(
         async_get_clientsession(self.hass), account_id, password
     )
     if token is None:
         _LOGGER.debug("Adax: Failed to login to retrieve token")
         errors["base"] = "cannot_connect"
         return self.async_show_form(
             step_id="cloud",
             data_schema=data_schema,
             errors=errors,
         )
     ```
     This allows the user to correct their credentials and try again.
   - Only if a `token` is successfully retrieved does the flow proceed to `self.async_create_entry(...)`.

In both scenarios, a connection/authentication attempt is made, and failures are communicated to the user *before* the config entry is created, aligning perfectly with the requirements of the `test-before-configure` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:08:08. Prompt tokens: 6869, Output tokens: 1011, Total tokens: 10360_
