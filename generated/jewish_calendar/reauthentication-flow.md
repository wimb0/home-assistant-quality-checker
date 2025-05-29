# jewish_calendar: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not require any form of authentication. It configures based on location, timezone, and user preferences for local calculations. |

## Overview

The `reauthentication-flow` rule mandates that integrations requiring authentication (e.g., API tokens, passwords for external services or devices) must provide a UI flow for users to update their credentials if they change or become invalid. This avoids the need for users to delete and re-add the integration.

This rule does **not apply** to the `jewish_calendar` integration.

The `jewish_calendar` integration is classified as `"iot_class": "calculated"` in its `manifest.json`. It relies on the `hdate` library for performing date and time calculations specific to the Jewish calendar. The configuration process, as defined in `config_flow.py`, involves setting parameters such as:
*   `CONF_DIASPORA` (boolean for location relative to Israel)
*   `CONF_LANGUAGE`
*   `CONF_LOCATION` (latitude and longitude)
*   `CONF_ELEVATION`
*   `CONF_TIME_ZONE`

The `_get_data_schema` function in `config_flow.py` clearly shows these parameters:
```python
async def _get_data_schema(hass: HomeAssistant) -> vol.Schema:
    # ...
    return vol.Schema(
        {
            vol.Required(CONF_DIASPORA, default=DEFAULT_DIASPORA): BooleanSelector(),
            vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): LanguageSelector(
                LanguageSelectorConfig(languages=list(get_args(Language)))
            ),
            vol.Optional(CONF_LOCATION, default=default_location): LocationSelector(),
            vol.Optional(CONF_ELEVATION, default=hass.config.elevation): int,
            vol.Optional(CONF_TIME_ZONE, default=hass.config.time_zone): SelectSelector(
                SelectSelectorConfig(options=get_timezones, sort=True)
            ),
        }
    )
```
None of these configuration options represent authentication credentials for an external service or device. The integration does not connect to any external services that would require such credentials to be maintained or re-validated.

The `config_flow.py` file does implement `async_step_reconfigure`, but this is for changing the existing configuration parameters (like location or language), not for re-authentication, which is not applicable.

Since the integration does not use any form of authentication, the requirement for a reauthentication flow is not relevant.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:20:39. Prompt tokens: 13986, Output tokens: 686, Total tokens: 16201_
