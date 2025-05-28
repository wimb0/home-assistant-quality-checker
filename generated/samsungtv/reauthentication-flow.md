```markdown
# samsungtv: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **done**                                                                 |

## Overview

This rule requires integrations that depend on external authentication to provide a reauthentication flow via the Home Assistant UI when credentials become invalid. This allows the user to update their credentials without needing to remove and re-add the integration.

The `samsungtv` integration uses authentication methods (popup on the TV for standard/websocket connections, and a PIN for encrypted websocket connections), making this rule applicable.

The integration fully implements the reauthentication flow:

1.  **Triggering Reauthentication:** The `SamsungTVBridge` class includes an `auth_failed` attribute and a `_notify_reauth_callback` method. In `homeassistant/components/samsungtv/__init__.py`, the `async_setup_entry` function registers a callback function (`_access_denied`) with the bridge using `bridge.register_reauth_callback(_access_denied)`. This callback, when invoked by the bridge upon an authentication failure, calls `entry.async_start_reauth(hass)`, which correctly initiates the reauthentication flow in the UI. This is evident in the `SamsungTVLegacyBridge` and `SamsungTVWSBridge` classes where `self.auth_failed = True` and `self._notify_reauth_callback()` are called in exception handlers (`AccessDenied`, `UnauthorizedError`).

2.  **Config Flow Steps:** The `SamsungTVConfigFlow` class in `homeassistant/components/samsungtv/config_flow.py` includes the required `async_step_reauth` and `async_step_reauth_confirm` methods.
    *   `async_step_reauth` simply forwards to `async_step_reauth_confirm`.
    *   `async_step_reauth_confirm` checks the authentication `CONF_METHOD` from the config entry.
        *   If the method is `METHOD_ENCRYPTED_WEBSOCKET`, it proceeds to `async_step_reauth_confirm_encrypted`.
        *   For other methods (standard websocket/legacy), it attempts to connect using `self._bridge.async_try_connect()`. If successful (`RESULT_SUCCESS`), it updates the config entry with any new token received and uses `self.async_update_reload_and_abort` to update the entry and trigger a reload. If connection fails due to authentication issues (`RESULT_AUTH_MISSING` or `RESULT_CANNOT_CONNECT`), it presents an error form.
    *   `async_step_reauth_confirm_encrypted` handles the encrypted method. It starts the encrypted pairing process, shows a form to collect the PIN (`data_schema=vol.Schema({vol.Required(CONF_PIN): str})`), uses the provided PIN to get a token and session ID via the authenticator, and if successful, updates the config entry using `self.async_update_reload_and_abort`.

The implementation correctly adapts the reauthentication steps based on the specific authentication method required by the TV model, providing a form for PIN input where necessary and relying on the TV's own popup prompt for other methods, while still validating connectivity.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:30:47. Prompt tokens: 30653, Output tokens: 783, Total tokens: 32604_
