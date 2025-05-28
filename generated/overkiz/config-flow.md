# overkiz: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `config-flow` rule requires that an integration can be set up via the Home Assistant user interface. This involves having `config_flow: true` in the `manifest.json`, a `config_flow.py` file implementing the setup logic, and a `strings.json` file for UI text, including descriptions for input fields.

The `overkiz` integration adheres to this rule:

1.  **Manifest Configuration**: The `manifest.json` file correctly includes `"config_flow": true`.
    ```json
    // homeassistant/components/overkiz/manifest.json
    {
      "domain": "overkiz",
      "name": "Overkiz",
      "config_flow": true,
      // ...
    }
    ```

2.  **Config Flow Implementation (`config_flow.py`)**:
    *   The integration provides a `config_flow.py` file with a class `OverkizConfigFlow` that inherits from `ConfigFlow`.
    *   It implements `async_step_user` to initiate the flow, allowing users to select their server (hub).
    *   It offers conditional steps (`async_step_local_or_cloud`) for users to choose between local and cloud API connections if their hub supports it.
    *   Separate steps for cloud (`async_step_cloud`) and local (`async_step_local`) setup are well-defined, collecting necessary credentials (username/password for cloud, host/token/verify_ssl for local).
    *   Input validation is performed in `async_validate_input` by attempting to log in with the provided credentials and catching various exceptions (e.g., `BadCredentialsException`, `TooManyRequestsException`, `ClientError`).
    *   Error messages are provided to the user through the `errors` dictionary in `async_show_form`.
    *   Discovery is supported via `async_step_dhcp` and `async_step_zeroconf`.
    *   Reauthentication is handled by `async_step_reauth`.
    *   Unique IDs are set to prevent duplicate configurations using `self.async_set_unique_id`.
    *   Configuration data is stored in `ConfigEntry.data` upon successful setup using `self.async_create_entry(..., data=user_input)`. All collected parameters (`CONF_HUB`, `CONF_API_TYPE`, `CONF_USERNAME`, `CONF_PASSWORD`, `CONF_HOST`, `CONF_TOKEN`, `CONF_VERIFY_SSL`) are essential for establishing a connection and are appropriately stored in `data`.

3.  **UI Text and Descriptions (`strings.json`)**:
    *   The `strings.json` file contains a `config` section with translations for flow titles, step descriptions, data field labels, and data field descriptions.
    *   Specifically, `data_description` is provided for each input field in all steps (`user`, `local_or_cloud`, `cloud`, `local`), giving users context about the required input, as recommended by the rule. For example:
        ```json
        // homeassistant/components/overkiz/strings.json
        "config": {
          "step": {
            "user": {
              "data": {
                "hub": "Server"
              },
              "data_description": {
                "hub": "Select the mobile app that you use to control your devices."
              }
            },
            // ... other steps with data and data_description
          }
        }
        ```
    *   Error and abort messages are also defined, enhancing user experience.

4.  **Selectors and User-Friendliness**:
    *   Appropriate Voluptuous schema elements are used, leading to suitable UI selectors (e.g., `vol.In` for dropdowns/radio buttons for `CONF_HUB` and `CONF_API_TYPE`, `str` for text inputs, `bool` for checkboxes).

The integration fully implements the requirements for UI-based setup, including handling different connection types, discovery, reauthentication, and providing clear user guidance through `strings.json`.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:09:51. Prompt tokens: 87293, Output tokens: 1024, Total tokens: 91832_
