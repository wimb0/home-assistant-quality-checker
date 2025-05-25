```markdown
# fritzbox: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **done**                                      |
| Reason |                                                                          |

## Overview

This rule requires integrations to be set up via the Home Assistant UI using a config flow, ensuring a consistent and user-friendly setup experience. It also mandates that configuration needed for connection is stored in `ConfigEntry.data` and other settings in `ConfigEntry.options`, and that strings/descriptions are handled via `strings.json` including `data_description`.

The `fritzbox` integration fully complies with this rule.

1.  **Config Flow Presence:** The `manifest.json` file (`homeassistant/components/fritzbox/manifest.json`) contains the entry `"config_flow": true`, indicating that it supports UI setup via a config flow.
2.  **`config_flow.py` Implementation:** The integration provides a `config_flow.py` file (`homeassistant/components/fritzbox/config_flow.py`) which defines `FritzboxConfigFlow` inheriting from `ConfigFlow`.
3.  **Setup Steps:** The flow implements the required `async_step_user` for manual configuration, allowing the user to input the host, username, and password. It also correctly handles discovery via `async_step_ssdp`, confirmation via `async_step_confirm`, reauthentication via `async_step_reauth` and `async_step_reauth_confirm`, and reconfiguration via `async_step_reconfigure`.
4.  **Data Storage:** The configuration data (host, username, password) needed for connecting to the FRITZ!Box is correctly stored in `ConfigEntry.data` using `self.async_create_entry(title=name, data=...)` in `_get_entry` and updated via `self.async_update_reload_and_abort(..., data_updates=...)` in `async_step_reconfigure`. The integration does not configure any settings via the flow that would typically belong in `options`.
5.  **Input Validation and Error Handling:** The flow includes an `async_try_connect` method which validates the provided credentials and host accessibility, returning specific error codes (`RESULT_INVALID_AUTH`, `RESULT_NO_DEVICES_FOUND`, `RESULT_NOT_SUPPORTED`, `RESULT_SUCCESS`). These errors are handled in the steps (`async_step_user`, `async_step_confirm`, `async_step_reauth_confirm`, `async_step_reconfigure`) using `errors["base"] = result` and `self.async_show_form`, providing feedback to the user. Abort reasons are handled via `self.async_abort`.
6.  **String Management:** The `strings.json` file (`homeassistant/components/fritzbox/strings.json`) defines all user-facing strings for the config flow steps, including `data_description` for input fields like `host`. This ensures proper internationalization and user guidance.

The code demonstrates a well-structured and comprehensive config flow implementation covering manual setup, discovery, reauthentication, and reconfiguration, and correctly handles configuration data and user-facing strings according to the rule's requirements.

## Suggestions

No suggestions needed. The integration already follows the rule.
```

_Created at 2025-05-25 11:19:57. Prompt tokens: 19284, Output tokens: 787, Total tokens: 21141_
