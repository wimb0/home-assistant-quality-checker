# jewish_calendar: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **todo**                                                                 |

## Overview

The `reconfiguration-flow` rule requires that integrations with user-configurable settings provide a way for users to modify these settings after the initial setup, without needing to delete and re-add the integration.

This rule applies to the `jewish_calendar` integration because:
1.  It uses a config flow (`"config_flow": true` in `manifest.json`).
2.  The initial configuration (`async_step_user` in `config_flow.py`) collects several user-configurable settings such as diaspora status, language, location, elevation, and time zone, as defined in the `_get_data_schema` function. These are settings a user might legitimately want to change.

The `jewish_calendar` integration attempts to implement a reconfiguration flow. It includes an `async_step_reconfigure` method in its `config_flow.py`:
```python
# homeassistant/components/jewish_calendar/config_flow.py
# ...
    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        reconfigure_entry = self._get_reconfigure_entry()
        if not user_input:
            return self.async_show_form(
                data_schema=self.add_suggested_values_to_schema(
                    await _get_data_schema(self.hass),
                    reconfigure_entry.data,
                ),
                step_id="reconfigure",
            )

        return self.async_update_reload_and_abort(reconfigure_entry, data=user_input)
# ...
```
This method correctly displays a form pre-filled with existing data (for most fields) and uses `async_update_reload_and_abort` to save the updated data and reload the integration.

However, the integration does **NOT fully follow** the rule due to a specific issue in handling location data during reconfiguration:
The `async_step_user` method correctly processes the `CONF_LOCATION` input (which is a dictionary from the `LocationSelector`) and extracts `CONF_LATITUDE` and `CONF_LONGITUDE` into the top level of the data to be saved:
```python
# homeassistant/components/jewish_calendar/config_flow.py (async_step_user)
            if CONF_LOCATION in user_input:
                user_input[CONF_LATITUDE] = user_input[CONF_LOCATION][CONF_LATITUDE]
                user_input[CONF_LONGITUDE] = user_input[CONF_LOCATION][CONF_LONGITUDE]
            # user_input now contains top-level CONF_LATITUDE and CONF_LONGITUDE
            return self.async_create_entry(title=DEFAULT_NAME, data=user_input)
```
The `async_setup_entry` method in `__init__.py` relies on these top-level `CONF_LATITUDE` and `CONF_LONGITUDE` keys:
```python
# homeassistant/components/jewish_calendar/__init__.py
# ...
            latitude=config_entry.data.get(CONF_LATITUDE, hass.config.latitude),
            longitude=config_entry.data.get(CONF_LONGITUDE, hass.config.longitude),
# ...
```
The `async_step_reconfigure` method, however, lacks this processing step for `user_input`. When the form is submitted, `user_input` contains `CONF_LOCATION` as a dictionary but does not have `CONF_LATITUDE` and `CONF_LONGITUDE` as separate top-level keys. The call `self.async_update_reload_and_abort(reconfigure_entry, data=user_input)` replaces the entire `config_entry.data` with this `user_input`. Consequently, when `async_setup_entry` is subsequently called, it will not find the top-level `CONF_LATITUDE` and `CONF_LONGITUDE` keys (or they might be stale if not overwritten), and the location will likely default to Home Assistant's global coordinates, effectively ignoring the user's updated location from the reconfiguration flow.

Because the reconfiguration flow does not correctly update the location, the integration does not fully allow users to update all its configurations, thus a "todo" status is assigned.

## Suggestions

To make the `jewish_calendar` integration compliant with the `reconfiguration-flow` rule by ensuring location updates are correctly processed, the `async_step_reconfigure` method in `config_flow.py` needs to be modified.

Specifically, before calling `self.async_update_reload_and_abort`, the `user_input` should be processed to extract `CONF_LATITUDE` and `CONF_LONGITUDE` from the `CONF_LOCATION` dictionary, similar to how it's done in `async_step_user`.

**Proposed change in `homeassistant/components/jewish_calendar/config_flow.py`:**

```python
    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        reconfigure_entry = self._get_reconfigure_entry()
        if not user_input:
            # Pre-fill logic:
            # Create a mutable copy of the current data to adjust for the form schema.
            current_data = dict(reconfigure_entry.data)
            # Ensure CONF_LOCATION is populated for the LocationSelector if only lat/lon exist.
            if CONF_LOCATION not in current_data and CONF_LATITUDE in current_data and CONF_LONGITUDE in current_data:
                current_data[CONF_LOCATION] = {
                    CONF_LATITUDE: current_data[CONF_LATITUDE],
                    CONF_LONGITUDE: current_data[CONF_LONGITUDE],
                }

            return self.async_show_form(
                data_schema=self.add_suggested_values_to_schema(
                    await _get_data_schema(self.hass),
                    current_data, # Use adjusted current_data
                ),
                step_id="reconfigure",
                # Add description placehoders for reconfigure if not already present in strings.json
                # For example, using reconfigure_successful abort for success message
                description_placeholders={"name": reconfigure_entry.title or DEFAULT_NAME}
            )

        # Process user_input to extract latitude and longitude
        if CONF_LOCATION in user_input and isinstance(user_input[CONF_LOCATION], dict):
            user_input[CONF_LATITUDE] = user_input[CONF_LOCATION].get(CONF_LATITUDE)
            user_input[CONF_LONGITUDE] = user_input[CONF_LOCATION].get(CONF_LONGITUDE)
            # It's good practice to remove the composite CONF_LOCATION if it's fully represented
            # by top-level keys, or ensure async_setup_entry can handle its presence.
            # For consistency with async_step_user, which keeps it, we can keep it too.
            # If only top-level keys are desired in config_entry.data:
            # user_input.pop(CONF_LOCATION)

        self.hass.config_entries.async_update_entry(
            reconfigure_entry, data=user_input
        )
        # Use self.async_abort with reason "reconfigure_successful"
        # if you want to show a success message and not immediately reload.
        # self.async_update_reload_and_abort reloads and then aborts.
        return self.async_abort(reason="reconfigure_successful")
```

**Explanation of Suggested Changes:**

1.  **Pre-filling the form:**
    *   The code now explicitly creates `current_data` from `reconfigure_entry.data`.
    *   It checks if `CONF_LOCATION` (the dictionary structure expected by `LocationSelector`) exists. If not, but `CONF_LATITUDE` and `CONF_LONGITUDE` do (e.g., from an older setup or if `async_step_user` only saved those), it constructs the `CONF_LOCATION` dictionary. This ensures the `LocationSelector` is correctly pre-filled with the *actual* configured location, not HA's default.
    *   Pass this `current_data` to `add_suggested_values_to_schema`.

2.  **Processing `user_input`:**
    *   After the user submits the form, and `user_input` is received, the code now includes the crucial block:
        ```python
        if CONF_LOCATION in user_input and isinstance(user_input[CONF_LOCATION], dict):
            user_input[CONF_LATITUDE] = user_input[CONF_LOCATION].get(CONF_LATITUDE)
            user_input[CONF_LONGITUDE] = user_input[CONF_LOCATION].get(CONF_LONGITUDE)
        ```
    *   This ensures that `CONF_LATITUDE` and `CONF_LONGITUDE` are present as top-level keys in the `user_input` dictionary that will become the new `config_entry.data`. This matches what `async_setup_entry` expects.

3.  **Updating and Aborting:**
    *   The example uses `self.hass.config_entries.async_update_entry(...)` followed by `self.async_abort(reason="reconfigure_successful")`. This pattern is common and typically preferred as `async_update_reload_and_abort` is a convenience that might not always be suitable if more control over the abort step is needed. However, `async_update_reload_and_abort(reconfigure_entry, data=user_input)` is also acceptable if `user_input` is correctly prepared. The primary fix is the data preparation.
    *   The original `return self.async_update_reload_and_abort(reconfigure_entry, data=user_input)` is fine *as long as `user_input` has been correctly modified* as per point 2.

By implementing these changes, the `CONF_LOCATION` data will be handled consistently across initial setup and reconfiguration, allowing users to reliably update their location settings. This will make the integration fully compliant with the `reconfiguration-flow` rule.

_Created at 2025-05-29 08:31:02. Prompt tokens: 13942, Output tokens: 2430, Total tokens: 22703_
