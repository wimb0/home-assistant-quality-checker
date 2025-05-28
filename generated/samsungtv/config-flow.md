```markdown
# samsungtv: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule requires integrations to be configurable via the Home Assistant UI using a configuration flow, promoting a consistent and user-friendly setup experience. This includes having a `config_flow.py` file, declaring support in `manifest.json`, using `strings.json` for UI text, storing configuration in `ConfigEntry.data` (and options in `ConfigEntry.options` if applicable), and supporting relevant flows like discovery and reauthentication.

The `samsungtv` integration fully complies with this rule.

1.  **`manifest.json`**: The integration's `manifest.json` file explicitly sets `"config_flow": true`, indicating its support for UI configuration.
2.  **`config_flow.py`**: The `homeassistant/components/samsungtv/config_flow.py` file exists and defines the `SamsungTVConfigFlow` class, which inherits from `ConfigFlow`.
3.  **Setup Flows**: The `config_flow.py` implements the required flows:
    *   `async_step_user`: Handles manual setup initiated by the user, prompting for the host.
    *   `async_step_ssdp`, `async_step_dhcp`, `async_step_zeroconf`: Handles discovery via these protocols, automatically initiating the flow.
    *   `async_step_confirm`: Used after discovery to allow the user to confirm the discovered device.
    *   `async_step_pairing`, `async_step_encrypted_pairing`: Guides the user through the authentication process (accepting on TV or entering PIN) depending on the detected connection method.
4.  **Reauthentication Flow**: The integration implements `async_step_reauth`, `async_step_reauth_confirm`, and `async_step_reauth_confirm_encrypted` to handle reauthentication when access is denied, as seen in the `SamsungTVBridge` `_notify_reauth_callback` which calls `entry.async_start_reauth(hass)`.
5.  **Configuration Storage**: The flow uses `self.async_create_entry` and `self.hass.config_entries.async_update_entry` to store necessary configuration data like `CONF_HOST`, `CONF_MAC`, `CONF_METHOD`, `CONF_TOKEN`, `CONF_SESSION_ID`, etc., directly within the `ConfigEntry.data` dictionary, which is appropriate for connection-related information. There are no evident parameters currently handled by the integration that should be stored in `ConfigEntry.options` instead.
6.  **UI Text and Descriptions**: The `strings.json` file provides localized text for all config flow steps, errors, and abort reasons. It also includes `data_description` for input fields like `host` and `pin`, offering extra context to the user during setup.
7.  **Flow Transitions**: The flow correctly utilizes `ConfigFlowResult` objects (`async_show_form`, `async_create_entry`, `async_abort`) to manage the flow state and transitions.

The integration demonstrates a robust implementation of a config flow, addressing manual configuration, discovery, authentication, and reauthentication, adhering to the requirements of this rule.

## Suggestions

No suggestions needed. The integration fully complies with the `config-flow` rule.
```

_Created at 2025-05-25 11:28:01. Prompt tokens: 30427, Output tokens: 827, Total tokens: 32244_
