# jewish_calendar: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-configure` rule requires that integrations test the validity of user-provided configuration data within the config flow, before the configuration entry is created. This is to catch issues early and provide immediate feedback to the user, preventing the setup of a non-functional integration. Issues can include invalid credentials, network problems, or, as relevant here, unsupported configurations or parameters that cause the underlying library to fail.

This rule applies to the `jewish_calendar` integration. Although `jewish_calendar` is an `iot_class: "calculated"` integration (meaning it primarily performs calculations rather than connecting to an external device or service), its core functionality relies on the `hdate` library. The `hdate` library, in turn, uses astronomical calculations (via its `astral` dependency) based on user-provided location (latitude, longitude, elevation) and time zone.
These astronomical calculations can fail or produce errors for certain combinations of input parameters, even if the parameters themselves are type-valid and within general ranges. For instance, calculating sun events (like sunrise or sunset, which are fundamental to Jewish calendar times/zmanim) might not be possible for extreme latitudes (e.g., polar regions) on certain dates, leading the `astral` library to raise a `ValueError`. This scenario is akin to an "unsupported device" or "unsupported configuration" that the rule aims to detect.

The `jewish_calendar` integration currently does **not** follow this rule.
In its `config_flow.py`, the `async_step_user` method collects user input and, if input is provided, directly proceeds to create the configuration entry without first attempting to validate if the provided parameters will work with the `hdate` library.

Specifically, in `homeassistant/components/jewish_calendar/config_flow.py`:
```python
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            if CONF_LOCATION in user_input:
                user_input[CONF_LATITUDE] = user_input[CONF_LOCATION][CONF_LATITUDE]
                user_input[CONF_LONGITUDE] = user_input[CONF_LOCATION][CONF_LONGITUDE]
            # No test call to hdate library with user_input is made here.
            return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        return self.async_show_form(
            # ...
        )
```
The call to `hdate.Location` and subsequently `hdate.Zmanim` happens later in `async_setup_entry` (in `__init__.py`). If this fails, the user gets a generic setup error, rather than specific feedback within the config flow.

## Suggestions

To make the `jewish_calendar` integration compliant with the `test-before-configure` rule, the `async_step_user` method in `config_flow.py` should be modified to test the user-provided configuration with the `hdate` library. This involves attempting to instantiate an `hdate.Location` object and, ideally, perform a basic calculation (like getting zmanim for the current day) to ensure the provided location parameters are usable.

Here's a conceptual example of how this could be implemented:

1.  **Import necessary modules** in `config_flow.py`:
    ```python
    import datetime
    from hdate import Location, Zmanim # Add Zmanim if not already imported
    from hdate.HDate import HDate # Potentially, if direct date interaction is needed for test
    from functools import partial # For running in executor
    ```

2.  **Modify `async_step_user`**:
    ```python
    # homeassistant/components/jewish_calendar/config_flow.py

    # ... (other imports)
    # Ensure _LOGGER is defined if not already:
    # import logging
    # _LOGGER = logging.getLogger(__name__)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Process CONF_LOCATION first as it's done currently
            processed_input = user_input.copy()
            if CONF_LOCATION in processed_input:
                processed_input[CONF_LATITUDE] = processed_input[CONF_LOCATION][CONF_LATITUDE]
                processed_input[CONF_LONGITUDE] = processed_input[CONF_LOCATION][CONF_LONGITUDE]
                # Do not remove CONF_LOCATION from processed_input if it's expected in the data dict
                # or ensure it's handled consistently if it should be replaced by lat/lon.
                # For creating the entry, it's often better to store the original user_input.

            try:
                # Extract parameters for the test, using HA defaults if not provided
                # Note: Config flow usually doesn't have direct access to hass.config like setup_entry.
                # It's better to make fields required or handle their absence explicitly.
                # For this example, we assume schema ensures presence or provides defaults.

                latitude = processed_input.get(
                    CONF_LATITUDE, self.hass.config.latitude
                )
                longitude = processed_input.get(
                    CONF_LONGITUDE, self.hass.config.longitude
                )
                # The schema defines elevation as optional with default from hass.config
                # However, in config flow, it's better if the schema provides a default
                # or the user is prompted. For testing, use hass.config if available.
                elevation = processed_input.get(
                    CONF_ELEVATION, self.hass.config.elevation
                )
                time_zone = processed_input.get(
                    CONF_TIME_ZONE, self.hass.config.time_zone
                )
                diaspora = processed_input.get(CONF_DIASPORA, DEFAULT_DIASPORA)

                # Perform the test using hdate library
                # This should be run in an executor as hdate/astral can be CPU-intensive
                
                def _validate_hdate_params():
                    # This is the actual test
                    loc = Location(
                        name="config_flow_test", # Temporary name for validation
                        diaspora=diaspora,
                        latitude=latitude,
                        longitude=longitude,
                        altitude=float(elevation), # hdate.Location expects float for altitude
                        timezone=time_zone,
                    )
                    # A more thorough test would be to try a calculation
                    _ = Zmanim(date=datetime.date.today(), location=loc)
                    # Potentially, even try to access a specific zman:
                    # _ = Zmanim(date=datetime.date.today(), location=loc).netz_hachama 

                await self.hass.async_add_executor_job(_validate_hdate_params)

            except ValueError as err: # astral often raises ValueError for invalid lat/lon/date combinations
                _LOGGER.warning("Jewish calendar configuration validation failed: %s", err)
                errors["base"] = "invalid_configuration" # Define this in strings.json
                                                        # e.g., "The_provided_location_parameters_are_invalid_or_unsupported_for_calculations."
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during Jewish calendar configuration validation")
                errors["base"] = "unknown" # Standard error key
            else:
                # If validation successful, create the entry with the original user_input
                return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        # Show form if no user_input or if errors occurred
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                await _get_data_schema(self.hass), user_input or {} # Pass empty dict if user_input is None
            ),
            errors=errors,
        )
    ```

3.  **Add error string(s)** to `strings.json`:
    For `"invalid_configuration"`:
    ```json
    {
      "config": {
        "error": {
          "invalid_configuration": "The provided location parameters are invalid or lead to calculation errors (e.g., for polar regions). Please check your latitude, longitude, elevation, and time zone.",
          // ... other errors
        },
        // ...
      }
    }
    ```
    And ensure `errors["base"] = "invalid_configuration"` in `async_step_user` maps to this string key (e.g., `errors["base"] = "invalid_configuration"`).

**Why these changes satisfy the rule:**
*   The code now attempts to use the core `hdate` library with the user's proposed settings *before* creating the config entry.
*   It specifically tries to instantiate `hdate.Location` and `hdate.Zmanim`, which are critical for the integration's operation. This directly tests if the geographical and time parameters are usable by the underlying astronomical calculation engine (`astral`).
*   If `hdate.Location(...)` or `hdate.Zmanim(...)` (or subsequent calls if added to the test) raise an exception (like `ValueError` from `astral` for polar regions where sun events might be undefined), this exception is caught.
*   Instead of proceeding to create a potentially broken entry, the user is shown the configuration form again with an error message, guiding them to correct the problematic input. This fulfills the rule's requirement to "test the connection" (in this case, to the calculation engine) and "return an error message to the user" if it fails.

_Created at 2025-05-29 08:10:20. Prompt tokens: 13676, Output tokens: 2373, Total tokens: 24019_
