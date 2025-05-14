# adax: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule mandates that integrations must be configurable through the Home Assistant UI using a config flow. This includes having a `config_flow.py`, setting `config_flow: true` in `manifest.json`, using `strings.json` for all UI text (including `data_description` for field context), and correctly storing configuration in `ConfigEntry.data` or `ConfigEntry.options`.

The `adax` integration **applies** to this rule as it is an integration that requires user configuration to connect to devices or cloud services.

The integration partially follows the rule:
*   It correctly sets `config_flow: true` in its `manifest.json`.
*   It implements a `config_flow.py` with logic to handle different connection types (Cloud and Local).
*   It uses `strings.json` for most UI text, including field labels (`data`), step descriptions (for most steps), error messages, and abort reasons.
*   It validates user input by attempting to connect to the Adax services or devices and provides feedback.
*   Configuration required for establishing connections (e.g., `ACCOUNT_ID`, `CONF_PASSWORD`, `CONF_IP_ADDRESS`, `CONF_TOKEN`) is stored in `ConfigEntry.data`. There are no apparent settings that would belong in `ConfigEntry.options`.

However, the integration does **not fully follow** the rule due to the following omissions in `strings.json`:
1.  **Missing `data_description`:** The rule explicitly requires the use of `data_description` within `strings.json` to provide context for each input field. This is missing for all fields in all config flow steps (`user`, `local`, `cloud`).
    For example, in `homeassistant/components/adax/strings.json`:
    ```json
    // For the "user" step:
    "user": {
      "data": {
        "connection_type": "Select connection type"
      },
      "description": "Select connection type. Local requires heaters with Bluetooth"
      // Missing: "data_description": { "connection_type": "Specify how to connect to your Adax heaters." }
    },
    // For the "local" step:
    "local": {
      "data": {
        "wifi_ssid": "Wi-Fi SSID",
        "wifi_pswd": "Wi-Fi password"
      },
      "description": "Reset the heater..."
      // Missing: "data_description": { "wifi_ssid": "The name (SSID) of your Wi-Fi network.", "wifi_pswd": "The password for your Wi-Fi network." }
    },
    // For the "cloud" step:
    "cloud": {
      "data": {
        "account_id": "Account ID",
        "password": "[%key:common::config_flow::data::password%]"
      }
      // Missing: "data_description": { "account_id": "Your Adax cloud account identifier.", "password": "The password for your Adax cloud account." }
    }
    ```

2.  **Missing step `description` for the `cloud` step:** While the `user` and `local` steps have a general `description`, the `cloud` step in `strings.json` is missing this element, which can aid user understanding.
    ```json
    // In homeassistant/components/adax/strings.json, under "cloud" step:
    "cloud": {
      "data": {
        "account_id": "Account ID",
        "password": "[%key:common::config_flow::data::password%]"
      }
      // Missing: "description": "Enter your Adax cloud account credentials."
    }
    ```

These omissions impact the user-friendliness and clarity of the configuration process, which is a key aspect of the `config-flow` rule.

## Suggestions

To make the `adax` integration compliant with the `config-flow` rule and improve user experience:

1.  **Add `data_description` for all input fields in `strings.json`:**
    For each step (`user`, `local`, `cloud`) and each field within those steps, add a `data_description` entry to provide specific context or instructions for that field.

    **Example for `homeassistant/components/adax/strings.json`:**
    ```json
    {
      "config": {
        "step": {
          "user": {
            "data": {
              "connection_type": "Select connection type"
            },
            "data_description": {
              "connection_type": "Choose 'Cloud' to connect via the Adax cloud service, or 'Local' for a direct connection to heaters (requires Bluetooth for initial local setup)."
            },
            "description": "Select connection type. Local requires heaters with Bluetooth"
          },
          "local": {
            "data": {
              "wifi_ssid": "Wi-Fi SSID",
              "wifi_pswd": "Wi-Fi password"
            },
            "data_description": {
              "wifi_ssid": "The name (SSID) of the Wi-Fi network the heater should connect to.",
              "wifi_pswd": "The password for the specified Wi-Fi network."
            },
            "description": "Reset the heater by pressing + and OK until display shows 'Reset'. Then press and hold OK button on the heater until the blue LED starts blinking before pressing Submit. Configuring heater might take some minutes."
          },
          "cloud": {
            "data": {
              "account_id": "Account ID",
              "password": "[%key:common::config_flow::data::password%]"
            },
            "data_description": {
              "account_id": "Your numerical Adax Account ID.",
              "password": "The password associated with your Adax Account ID."
            },
            "description": "Enter your Adax cloud account credentials to connect your heaters." // Also add this step description
          }
        }
        // ... rest of the file
      }
      // ... rest of the file
    }
    ```
    *Why:* This directly addresses the rule's requirement to "use `data_description` in the `strings.json` to give context about the input field," making the form more understandable.

2.  **Add a step `description` for the `cloud` step in `strings.json`:**
    Provide a general description for the `cloud` configuration step to guide the user.

    **Example snippet for the `cloud` step in `homeassistant/components/adax/strings.json`:**
    ```json
          "cloud": {
            "data": {
              "account_id": "Account ID",
              "password": "[%key:common::config_flow::data::password%]"
            },
            "data_description": { // As suggested above
              "account_id": "Your numerical Adax Account ID.",
              "password": "The password associated with your Adax Account ID."
            },
            "description": "Enter your Adax cloud account credentials to connect your heaters." // Add this line
          }
    ```
    *Why:* While not as critical as `data_description` for this specific rule, providing a step `description` enhances the overall user-friendliness of the config flow.

By implementing these changes, particularly the addition of `data_description` entries, the `adax` integration will fully comply with the `config-flow` rule's requirements for a clear and user-friendly setup process. Remember to update the corresponding translation files (e.g., `translations/en.json`) to reflect these changes.

_Created at 2025-05-14 15:04:53. Prompt tokens: 6953, Output tokens: 1837, Total tokens: 12524_
