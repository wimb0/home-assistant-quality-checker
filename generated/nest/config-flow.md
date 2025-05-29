# nest: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **todo**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `config-flow` rule requires integrations to be set up via the UI using a configuration flow. This flow should be user-friendly, validate input, use appropriate selectors, and provide contextual help for input fields using `data_description` in `strings.json`. All configuration necessary for connection should be stored in `ConfigEntry.data`, and other settings in `ConfigEntry.options`.

The `nest` integration **applies** to this rule as it's a user-facing integration that connects to an external service and devices.

The integration partially follows the rule:

1.  **`manifest.json` specifies `config_flow: true`**:
    ```json
    // homeassistant/components/nest/manifest.json
    {
      "domain": "nest",
      "name": "Google Nest",
      "config_flow": true,
      // ...
    }
    ```
    This is correct.

2.  **`config_flow.py` is implemented**:
    The file `homeassistant/components/nest/config_flow.py` exists and defines a multi-step OAuth2-based configuration flow (`NestFlowHandler`). This allows the integration to be set up via the UI.

3.  **User-friendly steps and input validation**:
    The config flow includes multiple steps (e.g., `async_step_cloud_project`, `async_step_device_project`, `async_step_pubsub_topic`) to guide the user. It uses `vol.Schema` for data input and includes error handling (e.g., checking if `project_id` and `cloud_project_id` are the same in `async_step_device_project`). It also uses `SelectSelector` for choices like topic and subscription names.

4.  **Configuration storage**:
    The config flow correctly stores the collected data (e.g., project IDs, token, subscription info) in `ConfigEntry.data` via `self.async_create_entry(title=title, data=self._data)`.

5.  **Presence of `CONFIG_SCHEMA` in `__init__.py`**:
    `homeassistant/components/nest/__init__.py` defines a `CONFIG_SCHEMA`. However, the `async_setup` function is minimal and does not appear to use this schema to set up the core SDM integration:
    ```python
    // homeassistant/components/nest/__init__.py
    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up Nest components with dispatch between old/new flows."""
        hass.http.register_view(NestEventMediaView(hass))
        hass.http.register_view(NestEventMediaThumbnailView(hass))
        return True
    ```
    Additionally, the official documentation for the Nest integration states that setup is entirely via the UI. Comments within the `CONFIG_SCHEMA` also refer to "old API" compatibility. This suggests the `CONFIG_SCHEMA` is likely for legacy purposes and not for the primary SDM API setup, which is handled by the config flow using Application Credentials. Therefore, its presence is not considered a violation for the current setup method.

6.  **Missing `data_description` in `strings.json`**:
    The rule emphasizes user-friendliness, stating: "use `data_description` in the `strings.json` to give context about the input field."
    While `strings.json` provides titles and general descriptions for steps, and labels for data fields (e.g., `config.step.cloud_project.data.cloud_project_id`), it lacks specific `data_description` entries for individual input fields. For example, in the `cloud_project` step:
    ```json
    // homeassistant/components/nest/strings.json
    "cloud_project": {
      "title": "Nest: Enter Cloud Project ID",
      "description": "Enter the Cloud Project ID below e.g. *example-project-12345*. See the [Google Cloud Console]({cloud_console_url}) or the documentation for [more info]({more_info_url}).",
      "data": {
        "cloud_project_id": "Google Cloud Project ID"
      }
      // Missing: "data_description": { "cloud_project_id": "Descriptive text for this field..." }
    }
    ```
    This omission means the integration does not fully meet the user-friendliness guidelines outlined in the rule.

7.  **Options Flow**:
    The rule states that settings not needed for the initial connection should be stored in `ConfigEntry.options` (typically managed via an options flow). There is no options flow implemented in `config_flow.py`. The legacy `CONFIG_SCHEMA` included items like `CONF_SENSORS` for `CONF_MONITORED_CONDITIONS`. If such filtering is still relevant for the SDM API and considered a post-setup setting, an options flow would be appropriate. However, if these are purely legacy or handled by entity enablement, then an options flow might not be necessary. The primary issue for "todo" status remains the `data_description`.

Due to the missing `data_description` for input fields in `strings.json`, the integration does not fully adhere to the user-friendliness aspect of the `config-flow` rule.

## Suggestions

To fully comply with the `config-flow` rule, specifically enhancing user-friendliness:

1.  **Add `data_description` for input fields in `strings.json`**:
    For each step in the config flow that requires user input via a text field (like `cloud_project_id` and `project_id`), add a corresponding `data_description` entry in `strings.json`. This provides users with more context directly related to the field they are filling out.

    **Example for `cloud_project_id` in `homeassistant/components/nest/strings.json`:**
    ```json
    // ...
    "config": {
      "step": {
        // ...
        "cloud_project": {
          "title": "Nest: Enter Cloud Project ID",
          "description": "Enter the Cloud Project ID below e.g. *example-project-12345*. See the [Google Cloud Console]({cloud_console_url}) or the documentation for [more info]({more_info_url}).",
          "data": {
            "cloud_project_id": "Google Cloud Project ID"
          },
          "data_description": {  // Add this section
            "cloud_project_id": "This is the Project ID from your Google Cloud Platform project, used for Pub/Sub and enabling the Smart Device Management API."
          }
        },
        "device_project": {
          "title": "Nest: Create a Device Access Project",
          "description": "Create a Nest Device Access project which **requires paying Google a US $5 fee** to set up.\n1. Go to the [Device Access Console]({device_access_console_url}), and through the payment flow.\n1. Select on **Create project**\n1. Give your Device Access project a name and select **Next**.\n1. Enter your OAuth Client ID\n1. Skip enabling events for now and select **Create project**.\n\nEnter your Device Access Project ID below ([more info]({more_info_url})).",
          "data": {
            "project_id": "Device Access Project ID"
          },
          "data_description": {  // Add this section
            "project_id": "This is the Project ID from the Google Nest Device Access Console. It's different from your Google Cloud Project ID."
          }
        }
        // ...
      }
    }
    // ...
    ```
    This change would make the config flow more understandable, aligning with the rule's requirements for a user-friendly setup process.

2.  **(Optional Review) Consider an Options Flow if applicable**:
    Review if any settings currently managed by legacy YAML configurations (like `CONF_SENSORS` or `CONF_BINARY_SENSORS` for filtering) are still relevant for the SDM API part of the integration. If they are, and they are not essential for the initial connection, they should be migrated to an options flow, storing their values in `ConfigEntry.options`. If these are entirely legacy and not applicable to SDM devices, then no options flow is needed for them.

_Created at 2025-05-28 22:50:46. Prompt tokens: 32653, Output tokens: 1993, Total tokens: 40704_
