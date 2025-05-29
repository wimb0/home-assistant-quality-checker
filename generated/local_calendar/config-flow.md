# local_calendar: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_calendar](https://www.home-assistant.io/integrations/local_calendar/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule requires integrations to be configurable via the UI using Home Assistant's config flow mechanism. This ensures a consistent and user-friendly setup experience. Key aspects include having a `config_flow.py`, setting `config_flow: true` in `manifest.json`, using `strings.json` for all UI text, storing configuration appropriately in `ConfigEntry.data` or `ConfigEntry.options`, and crucially, providing clear user guidance through `data_description` for input fields in `strings.json`.

This rule applies to the `local_calendar` integration as it is a standard, user-configurable integration that is not exempt under ADR-0010.

The `local_calendar` integration partially follows this rule:
*   `manifest.json` correctly sets `"config_flow": true`.
*   A `config_flow.py` is present and implements a two-step configuration flow (`user` and `import_ics_file`).
*   Configuration (`CONF_CALENDAR_NAME`, `CONF_STORAGE_KEY`) is stored in `ConfigEntry.data`.
*   Appropriate selectors (`SelectSelector`, `FileSelector`) are used.
*   Input validation is present (e.g., checking for existing calendar names, ICS file validation).
*   A `strings.json` file is present for UI text.

However, the integration does not fully meet the requirement for user-friendliness through `data_description` in `strings.json`:

1.  **Missing `data_description` for the `user` step:**
    In `strings.json`, under `config.step.user.data`, labels are provided for `calendar_name` and `import`. However, the corresponding `config.step.user.data_description` section, which provides helper text for these fields, is missing. The rule states: "...use `data_description` in the `strings.json` to give context about the input field."

2.  **Missing `data` and `data_description` for the `import_ics_file` step:**
    The `config_flow.py` defines `async_step_import_ics_file` which uses `step_id="import_ics_file"` and a schema `STEP_IMPORT_DATA_SCHEMA` requiring `CONF_ICS_FILE` (string key `"ics_file"`).
    The `strings.json` file has a section `config.step.import`. If this is intended for the `import_ics_file` step, it currently only contains a general `description`. It is missing the `data` sub-section for the `ics_file` field label and, more importantly for this rule, the `data_description` sub-section to provide context for the file upload field.
    Ideally, the key in `strings.json` should match the `step_id`, i.e., `config.step.import_ics_file`.

These omissions mean that users are not provided with helpful inline descriptions for the configuration fields, which can make the setup process less intuitive.

## Suggestions

To make the `local_calendar` integration fully compliant with the `config-flow` rule, the following changes to `homeassistant/components/local_calendar/strings.json` are recommended:

1.  **Add `data_description` for the `user` step:**
    Update the `user` step in `strings.json` to include descriptions for the `calendar_name` and `import` fields.

    ```diff
    --- a/homeassistant/components/local_calendar/strings.json
    +++ b/homeassistant/components/local_calendar/strings.json
    @@ -5,10 +5,18 @@
         "description": "Please choose a name for your new calendar",
         "data": {
           "calendar_name": "Calendar Name",
           "import": "Starting Data"
+        },
+        "data_description": {
+          "calendar_name": "The name for your new local calendar. This will be used to identify the calendar in Home Assistant.",
+          "import": "Choose whether to create an empty calendar or import events from an existing iCalendar (.ics) file."
         }
       },
       "import": {
+        "title": "Import iCalendar File",
         "description": "You can import events in iCal format (.ics file)."
       }
     },
    ```

2.  **Align `import_ics_file` step strings and add `data` / `data_description`:**
    It is best practice for the key in `strings.json` to match the `step_id` used in `config_flow.py` (`import_ics_file`). Add the necessary `data` and `data_description` for the `ics_file` field.

    Suggestion A (Preferred: Rename step key in `strings.json` to match `step_id`):
    ```diff
    --- a/homeassistant/components/local_calendar/strings.json
    +++ b/homeassistant/components/local_calendar/strings.json
    @@ -10,8 +10,17 @@
           "import": "Choose whether to create an empty calendar or import events from an existing iCalendar (.ics) file."
         }
       },
    -  "import": {
    -    "description": "You can import events in iCal format (.ics file)."
    +  "import_ics_file": {
    +    "title": "Import iCalendar File",
    +    "description": "Upload an iCalendar (.ics) file to import its events into the new local calendar.",
    +    "data": {
    +      "ics_file": "iCalendar File (.ics)"
    +    },
    +    "data_description": {
    +      "ics_file": "Select the .ics file from your computer to import. This file should contain calendar events in the iCalendar format."
    +    }
       }
     },
     "abort": {
    ```

    If renaming the step key from `"import"` to `"import_ics_file"` in `strings.json` is not desired for some reason, then modify the existing `"import"` section:

    Suggestion B (Modify existing `"import"` step key in `strings.json`):
    ```diff
    --- a/homeassistant/components/local_calendar/strings.json
    +++ b/homeassistant/components/local_calendar/strings.json
    @@ -10,7 +10,16 @@
           "import": "Choose whether to create an empty calendar or import events from an existing iCalendar (.ics) file."
         }
       },
       "import": {
    -    "description": "You can import events in iCal format (.ics file)."
    +    "title": "Import iCalendar File",
    +    "description": "Upload an iCalendar (.ics) file to import its events into the new local calendar.",
    +    "data": {
    +      "ics_file": "iCalendar File (.ics)"
    +    },
    +    "data_description": {
    +      "ics_file": "Select the .ics file from your computer to import. This file should contain calendar events in the iCalendar format."
    +    }
       }
     },
     "abort": {
    ```

By implementing these changes, the `local_calendar` integration will provide clearer guidance to users during setup, fulfilling the user-friendliness aspect of the `config-flow` rule.

_Created at 2025-05-28 23:24:18. Prompt tokens: 6737, Output tokens: 1792, Total tokens: 13385_
