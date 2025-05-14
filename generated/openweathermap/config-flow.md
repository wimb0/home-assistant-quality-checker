# openweathermap: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule requires integrations to be set up via the UI, using `config_flow.py` and `strings.json`, storing configuration appropriately in `ConfigEntry.data` and `ConfigEntry.options`, and ensuring the flow is user-friendly, including the use of `data_description` in `strings.json`.

This rule applies to the `openweathermap` integration as it is a user-facing integration that requires configuration (API key, location, etc.) and does not fall under the exemptions listed in ADR-0010.

The `openweathermap` integration partially follows the rule:
*   **UI Setup**: It can be set up via the UI. The `manifest.json` correctly includes `"config_flow": true`.
*   **`config_flow.py`**: A `config_flow.py` file is present, implementing `async_step_user` for initial setup and an `OptionsFlow` for managing settings.
*   **`strings.json`**: A `strings.json` file (and its translations) exists, providing UI text for the configuration and options flows.
*   **Input Validation**: The config flow validates the API key using the `validate_api_key` utility function (from `utils.py`) during the user setup step.

However, the integration does not fully follow the rule due to the following:

1.  **Missing `data_description` for User Input Fields**:
    The rule states: "we should use `data_description` in the `strings.json` to give context about the input field."
    The `homeassistant/components/openweathermap/strings.json` file defines labels for input fields under `config.step.user.data` but lacks the corresponding `config.step.user.data_description` section. This means users are not provided with per-field contextual help/descriptions directly in the UI, which can impact user-friendliness.

    For example, in `strings.json`:
    ```json
    // ...
    "step": {
      "user": {
        "data": {
          "api_key": "[%key:common::config_flow::data::api_key%]",
          "language": "[%key:common::config_flow::data::language%]",
          // ... other fields
        },
        // "data_description" section is missing here
        "description": "To generate API key go to https://openweathermap.org/appid" // This is a general step description
      }
    }
    // ...
    ```

2.  **Incorrect Storage of `CONF_MODE`**:
    The rule specifies: "The integration should store all configuration in the `ConfigEntry.data` field, while all settings that are not needed for the connection to be made should be stored in the `ConfigEntry.options` field."
    The `CONF_MODE` parameter (e.g., "v3.0", "current", "forecast") determines which OpenWeatherMap API version/endpoints are used. This is critical for how the integration "connects" and interacts with the service. The `pyopenweathermap.create_owm_client` function (used in `__init__.py`'s `async_setup_entry` and `utils.py`'s `validate_api_key`) directly uses the `mode`.

    Currently, `CONF_MODE` is treated as an option:
    *   `homeassistant/components/openweathermap/utils.py` in `build_data_and_options` explicitly separates `CONF_MODE` into the `options` dictionary using `OPTION_DEFAULTS = {CONF_LANGUAGE: DEFAULT_LANGUAGE, CONF_MODE: DEFAULT_OWM_MODE}`.
    *   `homeassistant/components/openweathermap/config_flow.py` allows `CONF_MODE` to be changed via the `OpenWeatherMapOptionsFlow`.
    *   `homeassistant/components/openweathermap/__init__.py` reads `mode` from `entry.options[CONF_MODE]`.

    Since `CONF_MODE` is essential for client initialization and API interaction (i.e., "needed for the connection to be made"), it should be stored in `ConfigEntry.data`. Storing it in `options` and allowing it to be changed post-setup without immediate re-validation of the API key (the options flow only reloads the entry) can lead to a broken integration if the existing API key is not valid for the newly selected mode.

## Suggestions

1.  **Add `data_description` to `strings.json` for User Input Fields**:
    To enhance user-friendliness and comply with the rule, provide contextual descriptions for each input field in the configuration flow.
    Modify `homeassistant/components/openweathermap/strings.json` by adding a `data_description` section within `config.step.user`:

    ```json
    {
      "config": {
        "step": {
          "user": {
            "data": {
              "api_key": "[%key:common::config_flow::data::api_key%]",
              "language": "[%key:common::config_flow::data::language%]",
              "latitude": "[%key:common::config_flow::data::latitude%]",
              "longitude": "[%key:common::config_flow::data::longitude%]",
              "mode": "[%key:common::config_flow::data::mode%]",
              "name": "[%key:common::config_flow::data::name%]"
            },
            "data_description": {
              "api_key": "Your API key from OpenWeatherMap. Ensure it matches the selected mode's requirements.",
              "language": "The language for weather data (e.g., 'en', 'de').",
              "latitude": "The latitude for the weather location.",
              "longitude": "The longitude for the weather location.",
              "mode": "The API mode to use (e.g., 'OneCall API v3.0' for full features, 'Free tier - Current weather' for basic current data). Some modes may require specific subscription tiers.",
              "name": "A unique name for this OpenWeatherMap instance."
            },
            "description": "To generate API key go to https://openweathermap.org/appid"
          }
        }
        // ... other sections
      }
      // ...
    }
    ```
    Ensure these new strings are also added to the translation files (e.g., `translations/en.json`).
    *Why*: This change will display helpful hints below each input field in the UI, guiding the user and improving the setup experience as stipulated by the rule.

2.  **Move `CONF_MODE` from `ConfigEntry.options` to `ConfigEntry.data`**:
    To correctly categorize `CONF_MODE` as essential connection configuration:

    *   **Modify `utils.py`**:
        In `homeassistant/components/openweathermap/utils.py`, update `OPTION_DEFAULTS` to exclude `CONF_MODE`:
        ```python
        OPTION_DEFAULTS = {CONF_LANGUAGE: DEFAULT_LANGUAGE} # Remove CONF_MODE
        ```
        This will ensure `build_data_and_options` places `CONF_MODE` (collected during initial setup) into the `data` dictionary.

    *   **Modify `__init__.py`**:
        In `homeassistant/components/openweathermap/__init__.py`, change how `mode` is accessed in `async_setup_entry`:
        ```python
        async def async_setup_entry(
            hass: HomeAssistant, entry: OpenweathermapConfigEntry
        ) -> bool:
            # ...
            language = entry.options[CONF_LANGUAGE]
            mode = entry.data[CONF_MODE] # Changed from entry.options[CONF_MODE]
            # ...
        ```

    *   **Modify `config_flow.py` (Options Flow)**:
        In `homeassistant/components/openweathermap/config_flow.py`, remove `CONF_MODE` from the schema in `OpenWeatherMapOptionsFlow`:
        ```python
        class OpenWeatherMapOptionsFlow(OptionsFlow):
            # ...
            def _get_options_schema(self):
                return vol.Schema(
                    {
                        # CONF_MODE section removed from here
                        vol.Optional(
                            CONF_LANGUAGE,
                            default=self.config_entry.options.get(
                                CONF_LANGUAGE, DEFAULT_LANGUAGE # Simplified default access
                            ),
                        ): vol.In(LANGUAGES),
                    }
                )
        ```

    *   **Verify Migration Logic**:
        The existing `async_migrate_entry` in `__init__.py` for versions `< 5` sets `CONF_MODE` in `combined_data` and then calls `build_data_and_options`. With the change to `utils.py`, `CONF_MODE` will correctly be placed into `new_data` during migration.

    *Why*: `CONF_MODE` dictates fundamental aspects of the API interaction and client setup, making it "needed for the connection to be made." Storing it in `ConfigEntry.data` aligns with the rule and ADR-0010. This makes the integration more robust because changing the mode (which could require a different API key or subscription) would necessitate deleting and re-adding the integration, forcing a full re-validation. While the `DeprecatedV25RepairFlow` currently modifies `CONF_MODE` in options, adherence to the `config-flow` rule for general configuration and options handling should prioritize this data/options split. The repair flow is an exceptional circumstance.

_Created at 2025-05-14 15:16:00. Prompt tokens: 14109, Output tokens: 2238, Total tokens: 25220_
