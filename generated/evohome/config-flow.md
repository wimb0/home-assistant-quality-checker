# evohome: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule mandates that integrations must be configurable via the UI using a config flow, ensuring a user-friendly setup process. This includes having a `config_flow.py`, a `manifest.json` with `"config_flow": true`, and defining UI text in `strings.json`, particularly using `data_description` for input field context. Configuration essential for connection should be in `ConfigEntry.data`, while other settings go into `ConfigEntry.options`.

The `evohome` integration partially adheres to this rule.
It **does** have:
1.  A `manifest.json` file with `"config_flow": true`.
2.  A `config_flow.py` file that implements `EvoConfigFlow` with steps like `async_step_user`, `async_step_location`, `async_step_import`, `async_step_reauth`, and `async_step_reconfigure`.
3.  An options flow handler (`EvoOptionsFlowHandler`) for configuring settings like scan interval and high precision.
4.  It uses `vol.Schema` for data validation and appropriate selectors (`TextSelector`, `NumberSelector`, `BooleanSelector`) for user input.
5.  It correctly separates essential connection parameters (username, password, location_idx, token_data) into `ConfigEntry.data` and other settings (scan_interval, high_precision) into `ConfigEntry.options`.
    *   See `config_flow.py`, `_update_or_create_entry()` and `DEFAULT_OPTIONS`.
6.  It has a `strings.json` file defining text for the config flow steps (e.g., `user`, `location`).
7.  It supports YAML import through the config flow (`async_setup` in `__init__.py` and `async_step_import` in `config_flow.py`).

However, the integration does **not fully** follow the rule because:
1.  **Missing `data_description` in `strings.json` for config flow steps:** The rule explicitly states "use `data_description` in the `strings.json` to give context about the input field."
    *   In `homeassistant/components/evohome/strings.json`, under `config.step.user` and `config.step.location`, there are `data` blocks for field labels (e.g., `username`, `password`, `location_idx`) and a general `description` for the step itself, but there is no `data_description` block to provide specific context for each individual input field.
    *   For example, for the `user` step:
        ```json
        "user": {
          "title": "User credentials",
          "data": {
            "username": "[%key:common::config_flow::data::username%]",
            "password": "[%key:common::config_flow::data::password%]"
          },
          "description": "Provide the logon details of your TCC account"
          // Missing "data_description": { "username": "...", "password": "..." }
        }
        ```

2.  **Missing string definitions for options flow in `strings.json`:** The options flow defined in `EvoOptionsFlowHandler` (in `config_flow.py`) presents a form to the user with fields like `CONF_HIGH_PRECISION` and `CONF_SCAN_INTERVAL`.
    *   The `strings.json` file does not contain an `options` block to define the title, field labels (`data`), or contextual descriptions (`data_description`) for this options flow step. This means the UI will likely use default labels derived from constant names, and no specific descriptions will be available for these options, which is contrary to the rule's emphasis on user-friendliness.

Due to these omissions, particularly the lack of `data_description` for input fields in both the main config flow and the options flow within `strings.json`, the integration is not fully compliant.

## Suggestions

To make the `evohome` integration fully compliant with the `config-flow` rule, the following changes are recommended:

1.  **Add `data_description` for config flow steps in `strings.json`:**
    For each input field in the `config` section of `strings.json` (e.g., `user`, `location` steps), add a `data_description` block to provide context.

    *Example for the `user` step in `homeassistant/components/evohome/strings.json`:*
    ```json
    {
      "config": {
        "step": {
          "user": {
            "title": "User credentials",
            "data": {
              "username": "[%key:common::config_flow::data::username%]",
              "password": "[%key:common::config_flow::data::password%]"
            },
            "description": "Provide the logon details of your TCC account",
            "data_description": {  // Add this block
              "username": "Your email address registered with Honeywell Total Connect Comfort (TCC).",
              "password": "The password for your TCC account."
            }
          },
          "location": {
            "title": "Location index",
            "data": {
              "location_idx": "Location index"
            },
            "description": "Provide the index of the location to use",
            "data_description": { // Add this block
              "location_idx": "If your TCC account has multiple locations, specify the numerical index (starting from 0) for the desired location."
            }
          }
          // ... other steps like reauth_confirm should also have data_description if they have input fields
        }
      },
      // ... rest of the file
    }
    ```

2.  **Add string definitions for the options flow in `strings.json`:**
    Create an `options` block in `strings.json` to define the UI text for the options flow steps handled by `EvoOptionsFlowHandler`. This should include `title`, `data` for field labels, and `data_description` for context.

    *Example for the `init` step of the options flow in `homeassistant/components/evohome/strings.json`:*
    ```json
    {
      // ... config section ...
      "options": { // Add this section
        "step": {
          "init": {
            "title": "Evohome Options",
            "data": {
              "scan_interval": "Scan Interval (seconds)",
              "high_precision": "Enable High Precision Temperatures"
            },
            "data_description": {
              "scan_interval": "Frequency to poll the Evohome API for updates. Lower values update faster but increase API calls.",
              "high_precision": "Enable to fetch higher precision temperature readings. This may use a secondary API endpoint and potentially increase API usage."
            }
          }
        },
        "error": {
          // Define any option-flow specific errors if needed
        },
        "abort": {
          // Define any option-flow specific abort reasons if needed
        }
      },
      // ... services section ...
    }
    ```
    Ensure the `step_id` used in `async_show_form` for the options flow (e.g., `"init"`) matches the key in `strings.json`.

By implementing these suggestions, the `evohome` integration will provide clearer, more user-friendly configuration and options dialogs, fulfilling all requirements of the `config-flow` rule.

---

_Created at 2025-05-29 11:42:52. Prompt tokens: 22123, Output tokens: 1806, Total tokens: 26897._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
