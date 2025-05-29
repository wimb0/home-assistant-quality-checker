# local_todo: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule mandates that integrations should be configurable via the Home Assistant user interface. This is achieved by implementing a config flow, which provides a standardized and user-friendly setup experience. Key aspects include the presence of `config_flow.py`, appropriate `manifest.json` settings, use of `strings.json` for localization, and clear guidance for the user, including contextual descriptions for input fields.

This rule applies to the `local_todo` integration. The integration is designed to be set up through the UI, as evidenced by `config_flow: true` in its `manifest.json` and the inclusion of a `config_flow.py` file.

The `local_todo` integration generally adheres to the core requirements for implementing a config flow:
*   It includes a `config_flow.py` file with a `LocalTodoConfigFlow` class that handles the user setup step.
*   The `manifest.json` correctly declares `"config_flow": true`.
*   User-facing text is managed in `strings.json`.
*   The configuration data (specifically `CONF_TODO_LIST_NAME` and the derived `CONF_STORAGE_KEY`) is appropriately stored in `ConfigEntry.data`. Given that the list name is fundamental to the integration's operation (determining the storage file), it's correctly placed in `data` rather than `options`.

However, the integration does not fully meet the user-friendliness criteria emphasized by the rule. The rule states: "This means we should use the right selectors at the right place, validate the input where needed, and use `data_description` in the `strings.json` to give context about the input field."

While the `local_todo` integration uses basic validation via `voluptuous` for the `CONF_TODO_LIST_NAME`, it is missing the `data_description` for this field in its `strings.json` file.

As seen in `homeassistant/components/local_todo/strings.json`:
```json
{
  "title": "Local To-do",
  "config": {
    "step": {
      "user": {
        "description": "Please choose a name for your new To-do list",
        "data": {
          "todo_list_name": "To-do list name"
        },
        // "data_description" block is missing here
        "submit": "Create"
      }
    },
    "abort": {
      "already_configured": "[%key:common::config_flow::abort::already_configured_service%]"
    }
  }
}
```
The absence of a `data_description` block for the `todo_list_name` field means that users are not provided with specific context or help text directly associated with this input during the setup process. This is a specific requirement highlighted by the rule to ensure the config flow is "very user-friendly and understandable."

## Suggestions

To make the `local_todo` integration fully compliant with the `config-flow` rule, the following modification is recommended:

1.  **Add `data_description` to `strings.json`:**
    Incorporate a `data_description` block within the `user` step of the config flow in `strings.json`. This will provide users with helpful context for the `todo_list_name` input field.

    Modify `homeassistant/components/local_todo/strings.json` as follows:

    ```json
    {
      "title": "Local To-do",
      "config": {
        "step": {
          "user": {
            "description": "Please choose a name for your new To-do list",
            "data": {
              "todo_list_name": "To-do list name"
            },
            "data_description": {
              "todo_list_name": "Enter the desired name for your to-do list. This name will be displayed in Home Assistant and will also be used to generate a unique identifier for the storage file."
            },
            "submit": "Create"
          }
        },
        "abort": {
          "already_configured": "[%key:common::config_flow::abort::already_configured_service%]"
        }
      }
    }
    ```

    **Why this helps:**
    Adding the `data_description` field directly addresses the rule's requirement to "use `data_description` in the `strings.json` to give context about the input field." This enhancement makes the configuration process more intuitive and user-friendly by clarifying the purpose and implications of the "To-do list name."

_Created at 2025-05-28 23:27:54. Prompt tokens: 5362, Output tokens: 1137, Total tokens: 10056_
