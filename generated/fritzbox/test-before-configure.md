```markdown
# fritzbox: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires integrations that connect to external devices or services to perform a connection test during the config flow before a configuration entry is successfully created. This helps identify and report connection issues (like incorrect host, firewall problems, or invalid credentials) early to the user.

The `fritzbox` integration connects to a FRITZ!Box router to fetch device data and control smart home devices. Therefore, this rule is applicable.

Upon reviewing the `homeassistant/components/fritzbox/config_flow.py` file, the integration correctly implements this rule.

The `FritzboxConfigFlow` class contains an `async_try_connect` method (which calls the synchronous `_try_connect` method). This method creates a `pyfritzhome.Fritzhome` instance with the provided host, username, and password and attempts to log in and retrieve device data (`fritzbox.login()`, `fritzbox.get_device_elements()`). It specifically catches `LoginError`, `HTTPError`, and `OSError` exceptions, returning predefined status codes (`RESULT_INVALID_AUTH`, `RESULT_NOT_SUPPORTED`, `RESULT_NO_DEVICES_FOUND`) to indicate the nature of the failure.

These connection test methods are called in the relevant steps of the config flow *before* creating or updating a config entry:

1.  **`async_step_user`**: After collecting the user's host, username, and password, `await self.async_try_connect()` is called. If the result is `RESULT_SUCCESS`, the entry is created (`self._get_entry(self._name)`). If the result is `RESULT_INVALID_AUTH`, an error is shown on the form (`errors["base"] = result`). For other failure results, the flow is aborted (`self.async_abort(reason=result)`).
2.  **`async_step_confirm`**: Used after SSDP discovery. It collects username and password. Similar to `async_step_user`, it calls `await self.async_try_connect()` and handles the results appropriately before creating the entry.
3.  **`async_step_reauth_confirm`**: Handles reauthentication. It collects username and password, calls `await self.async_try_connect()`, and if successful, updates the existing entry. Failures result in the form being shown with an error or the flow being aborted.
4.  **`async_step_reconfigure`**: Handles changing the host. It collects the new host, uses the existing credentials, calls `await self.async_try_connect()`, and if successful, updates the existing entry. Failures result in the form being shown with an error.

This implementation ensures that a connection is successfully established and validated before the configuration is considered complete and a config entry is created or updated, fully satisfying the `test-before-configure` rule.

## Suggestions

No suggestions needed. The integration correctly implements the `test-before-configure` rule.
```

_Created at 2025-05-25 11:20:52. Prompt tokens: 19200, Output tokens: 763, Total tokens: 20789_
