# linkplay: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule mandates that integrations must be configurable through the Home Assistant UI using a config flow. This enhances user experience by providing a consistent setup process, guiding users, validating input, and offering clear descriptions for configuration fields. Key requirements include the presence of a `config_flow.py` file, `config_flow: true` in `manifest.json`, use of `strings.json` for UI text (including `data_description` for input fields), and correct storage of configuration in `ConfigEntry.data` (for connection parameters) and `ConfigEntry.options` (for other settings).

This rule applies to the `linkplay` integration as it is a user-facing integration that requires configuration (the host of the LinkPlay device) and is not exempt under ADR-0010.

The `linkplay` integration **fully follows** this rule.

1.  **UI Setup Capability**:
    *   The `manifest.json` file correctly sets `"config_flow": true`.
    *   A `config_flow.py` file is present, defining `LinkPlayConfigFlow`.

2.  **Config Flow Implementation**:
    *   The `LinkPlayConfigFlow` class implements `async_step_user` for manual configuration, prompting the user for the device's host/IP address.
    *   It also implements `async_step_zeroconf` and `async_step_discovery_confirm` to support automatic discovery of LinkPlay devices, simplifying the setup process.

3.  **User Experience**:
    *   Input validation is performed by attempting to connect to the specified host using `linkplay_factory_httpapi_bridge`. If the connection fails, an appropriate error (`cannot_connect`) is displayed to the user.
    *   The `strings.json` file is utilized for all user-facing text in the config flow, ensuring translatability and consistency.
        *   For the `user` step, `data_description` is provided for the `host` field:
            ```json
            "data_description": {
              "host": "The hostname or IP address of the LinkPlay device."
            }
            ```
        *   Placeholders like `{name}` are used in `flow_title` and `discovery_confirm` steps for better context.

4.  **Configuration Storage**:
    *   The primary configuration required for connection, `CONF_HOST`, is correctly stored in `config_entry.data` upon successful setup. This is evident in both `async_step_user` and `async_step_discovery_confirm` which call `self.async_create_entry` with `data={CONF_HOST: self.data[CONF_HOST]}`.
    *   The integration does not collect any settings during the initial config flow that are not essential for the connection. Therefore, the requirement to store non-connection settings in `ConfigEntry.options` is met by not having such settings in the initial flow. If user-configurable options (not affecting the core connection) were to be added post-setup, they would typically be managed via an options flow.

5.  **Selectors**:
    *   The only input field, `CONF_HOST`, uses a standard string input, which is appropriate for a hostname or IP address.

The integration demonstrates a well-implemented config flow, including support for discovery, clear user prompts, error handling, and correct use of localization and configuration entry data storage as per the rule's requirements for initial setup.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:09:53. Prompt tokens: 11930, Output tokens: 874, Total tokens: 16480_
