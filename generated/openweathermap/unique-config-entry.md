# openweathermap: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `unique-config-entry` rule applies to the `openweathermap` integration because it utilizes a configuration flow (`config_flow: true` in `manifest.json`) to allow users to set up the integration via the Home Assistant UI. The purpose of this rule is to prevent users from accidentally setting up the same device or service multiple times, which could lead to duplicated entities and other issues.

The `openweathermap` integration correctly follows this rule. It ensures that a configuration for a specific geographical location (defined by latitude and longitude) can only be set up once. This is implemented in its config flow (`homeassistant/components/openweathermap/config_flow.py`) using the unique identifier method.

Specifically, in the `async_step_user` method of the `OpenWeatherMapConfigFlow` class, the integration performs the following steps:
1.  It retrieves the latitude and longitude from the user input.
2.  It generates a unique ID for the config entry by combining these two values: `f"{latitude}-{longitude}"`.
3.  It then calls `await self.async_set_unique_id(f"{latitude}-{longitude}")` to associate this unique ID with the current configuration flow.
4.  Crucially, it immediately calls `self._abort_if_unique_id_configured()` which checks if a config entry with this `unique_id` already exists. If it does, the flow is aborted, preventing a duplicate setup.

Relevant code snippet from `homeassistant/components/openweathermap/config_flow.py`:
```python
    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        # ...
        if user_input is not None:
            latitude = user_input[CONF_LATITUDE]
            longitude = user_input[CONF_LONGITUDE]
            # ...

            await self.async_set_unique_id(f"{latitude}-{longitude}") # Sets the unique ID
            self._abort_if_unique_id_configured() # Checks and aborts if already configured

            # ...
            if not errors:
                # ...
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=data, options=options
                )
        # ...
```

This implementation directly aligns with the example provided in the rule documentation for using a unique identifier. The abort message for this scenario is `already_configured: "[%key:common::config_flow::abort::already_configured_location%]"` in `strings.json`, which is appropriately user-facing.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:20:52. Prompt tokens: 14442, Output tokens: 694, Total tokens: 16564_
