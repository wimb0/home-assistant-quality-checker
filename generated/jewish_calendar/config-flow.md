# jewish_calendar: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule mandates that integrations should be configurable through the Home Assistant UI using a config flow. This enhances user experience by providing a consistent setup process, allowing for guided configuration, input validation, and clear explanations for each setting. Key aspects include using `config_flow.py`, `manifest.json` settings, `strings.json` for localization and descriptions, and appropriate storage of configuration in `ConfigEntry.data` versus `ConfigEntry.options`.

This rule applies to the `jewish_calendar` integration as it is a user-facing integration requiring specific configuration (like location, diaspora status, language, and various offsets) and does not fall under the exceptions outlined in ADR-0010.

The `jewish_calendar` integration fully follows this rule.

**Evidence of Compliance:**

1.  **Manifest Configuration:**
    *   The `manifest.json` file correctly declares support for config flow:
        ```json
        "config_flow": true
        ```

2.  **Config Flow Implementation (`config_flow.py`):**
    *   A `config_flow.py` file is present.
    *   It defines `JewishCalendarConfigFlow` inheriting from `homeassistant.config_entries.ConfigFlow`.
    *   The `async_step_user` method is implemented to handle initial setup. It uses `self.async_show_form` to display the configuration form and `self.async_create_entry` to save the configuration.
        ```python
        # homeassistant/components/jewish_calendar/config_flow.py
        class JewishCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
            # ...
            async def async_step_user(
                self, user_input: dict[str, Any] | None = None
            ) -> ConfigFlowResult:
                # ...
                return self.async_show_form(
                    step_id="user",
                    data_schema=self.add_suggested_values_to_schema(
                        await _get_data_schema(self.hass), user_input
                    ),
                )
        ```
    *   An options flow (`JewishCalendarOptionsFlowHandler`) is implemented to allow users to change settings post-setup (e.g., candle lighting and Havdalah offsets). This is good practice for settings not essential for the initial connection/setup.
        ```python
        # homeassistant/components/jewish_calendar/config_flow.py
        class JewishCalendarOptionsFlowHandler(OptionsFlow):
            async def async_step_init(
                self, user_input: dict[str, str] | None = None
            ) -> ConfigFlowResult:
                # ...
                return self.async_show_form(
                    step_id="init",
                    data_schema=self.add_suggested_values_to_schema(
                        OPTIONS_SCHEMA, self.config_entry.options
                    ),
                )
        ```
    *   A reconfiguration flow (`async_step_reconfigure`) is also implemented, allowing users to modify the initial configuration.

3.  **User-Friendly Input with Selectors and Schema:**
    *   The configuration schema (`_get_data_schema`) and options schema (`OPTIONS_SCHEMA`) use `voluptuous` for defining fields and their types.
    *   Appropriate selectors are used to enhance user experience: `BooleanSelector`, `LanguageSelector`, `LocationSelector`, and `SelectSelector`.
        ```python
        # homeassistant/components/jewish_calendar/config_flow.py
        async def _get_data_schema(hass: HomeAssistant) -> vol.Schema:
            # ...
            return vol.Schema(
                {
                    vol.Required(CONF_DIASPORA, default=DEFAULT_DIASPORA): BooleanSelector(),
                    vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): LanguageSelector(
                        LanguageSelectorConfig(languages=list(get_args(Language)))
                    ),
                    vol.Optional(CONF_LOCATION, default=default_location): LocationSelector(),
                    # ...
                }
            )
        ```

4.  **Localization and Descriptions (`strings.json`):**
    *   The `strings.json` file provides translations and descriptions for configuration and options flow fields.
    *   Crucially, it includes `data_description` for each field, giving users context about the input, as required by the rule.
        ```json
        // homeassistant/components/jewish_calendar/strings.json
        "config": {
          "step": {
            "user": {
              "data": {
                "location": "[%key:common::config_flow::data::location%]",
                "diaspora": "[%key:component::jewish_calendar::common::diaspora%]",
                // ...
              },
              "data_description": {
                "location": "[%key:component::jewish_calendar::common::descr_location%]",
                "diaspora": "[%key:component::jewish_calendar::common::descr_diaspora%]",
                // ...
              }
            }
          }
        },
        "options": {
          "step": {
            "init": {
              "data": {
                "candle_lighting_minutes_before_sunset": "Minutes before sunset for candle lighting",
                // ...
              },
              "data_description": {
                "candle_lighting_minutes_before_sunset": "Defaults to 18 minutes. ...",
                // ...
              }
            }
          }
        }
        ```

5.  **Correct Data Storage:**
    *   Core configuration parameters essential for the calendar's calculations (location, diaspora status, language, timezone, elevation) are stored in `ConfigEntry.data`.
    *   Adjustable settings (candle lighting and Havdalah offsets) that are not strictly required for the basic setup are stored in `ConfigEntry.options`. This separation is correctly handled in `__init__.py` during `async_setup_entry`:
        ```python
        # homeassistant/components/jewish_calendar/__init__.py
        async def async_setup_entry(
            hass: HomeAssistant, config_entry: JewishCalendarConfigEntry
        ) -> bool:
            language = config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE) // from data
            diaspora = config_entry.data.get(CONF_DIASPORA, DEFAULT_DIASPORA) // from data
            candle_lighting_offset = config_entry.options.get( // from options
                CONF_CANDLE_LIGHT_MINUTES, DEFAULT_CANDLE_LIGHT
            )
            # ...
        ```

The integration demonstrates a comprehensive and correct implementation of the config flow, adhering to all specified requirements of the rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:05:29. Prompt tokens: 13760, Output tokens: 1656, Total tokens: 18015_
