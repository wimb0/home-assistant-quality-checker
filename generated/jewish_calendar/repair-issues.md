# jewish_calendar: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `repair-issues` rule requires integrations to use repair issues or repair flows when user intervention is needed to resolve a problem. These mechanisms should provide actionable and informative guidance to the user. Repair issues should not be raised for problems the user cannot fix.

This rule applies to the `jewish_calendar` integration because there are potential scenarios, primarily related to location configuration, where the integration might fail to operate correctly, and user intervention could resolve these issues.

The `jewish_calendar` integration currently does **NOT** follow this rule. It does not implement `homeassistant.helpers.issue_registry.async_create_issue` to inform users about fixable problems.

Specifically, there are two main areas where repair issues would be beneficial:

1.  **During Setup (`__init__.py`):**
    In `async_setup_entry`, the integration initializes `hdate.Location` using configured or Home Assistant's default location data:
    ```python
    # __init__.py
    location = await hass.async_add_executor_job(
        partial(
            Location,
            # ... location parameters ...
        )
    )
    ```
    If the `hdate.Location` constructor fails (e.g., due to invalid or problematic location data that causes calculation errors within the `hdate` library), the `async_setup_entry` will likely fail, and Home Assistant will raise `ConfigEntryNotReady`. While this prevents the integration from starting with bad data, it doesn't provide clear, actionable guidance to the user beyond log messages. A repair issue could direct the user to reconfigure the integration's location settings.

2.  **During Runtime Data Updates (`sensor.py`):**
    In `JewishCalendarBaseSensor.async_update_data`, the integration fetches astral event dates (e.g., sunset) which are crucial for its calculations:
    ```python
    # sensor.py
    event_date = get_astral_event_date(self.hass, SUN_EVENT_SUNSET, today)
    if event_date is None:
        _LOGGER.error("Can't get sunset event date for %s", today)
        return # Sensor update effectively fails silently for the user
    ```
    If `get_astral_event_date` returns `None` (e.g., due to an invalid or extreme location like polar regions where sunset is ill-defined), the integration currently logs an error and the sensor update process is aborted for that cycle. This can lead to stale or unavailable sensor states without clear indication to the user in the UI about the cause or how to fix it. A repair issue could inform the user that astral calculations are failing and suggest checking their location settings.

The integration has a reconfiguration flow (`async_step_reconfigure` in `config_flow.py`), making `is_fixable=True` repair issues particularly useful as they can guide the user directly to the necessary configuration adjustments.

## Suggestions

To make the `jewish_calendar` integration compliant with the `repair-issues` rule, the following changes are recommended:

1.  **Handle `hdate.Location` Initialization Errors during Setup:**
    Modify `__init__.py` to catch exceptions during `hdate.Location` initialization and create a repair issue.

    *   Import `issue_registry` and `ConfigEntryNotReady`:
        ```python
        from homeassistant.helpers import issue_registry as ir
        from homeassistant.exceptions import ConfigEntryNotReady
        ```
    *   In `async_setup_entry`, wrap the `hdate.Location` call in a try-except block:
        ```python
        # __init__.py
        try:
            location = await hass.async_add_executor_job(
                partial(
                    Location,
                    name=hass.config.location_name,
                    diaspora=diaspora,
                    latitude=config_entry.data.get(CONF_LATITUDE, hass.config.latitude),
                    longitude=config_entry.data.get(CONF_LONGITUDE, hass.config.longitude),
                    altitude=config_entry.data.get(CONF_ELEVATION, hass.config.elevation),
                    timezone=config_entry.data.get(CONF_TIME_ZONE, hass.config.time_zone),
                )
            )
            # If setup succeeds, clear any previous issue for this
            ir.async_delete_issue(hass, DOMAIN, "invalid_location_data")
        except Exception as ex:  # Ideally, catch more specific exceptions from hdate if known
            _LOGGER.error("Failed to initialize hdate.Location with provided configuration: %s", ex)
            ir.async_create_issue(
                hass,
                DOMAIN,
                "invalid_location_data",
                is_fixable=True,
                issue_domain=DOMAIN,  # Links to the integration's reconfigure flow
                severity=ir.IssueSeverity.ERROR,
                translation_key="invalid_location_data",
                translation_placeholders={"error_message": str(ex)},
                # learn_more_url: Optional, could point to documentation on location.
                config_entry_id=config_entry.entry_id,
            )
            raise ConfigEntryNotReady(
                f"Failed to initialize Jewish Calendar due to location data issue: {ex}"
            ) from ex
        ```
    *   Add corresponding translation keys to `strings.json` under a `repairs` section:
        ```json
        // strings.json
        {
          // ... other strings ...
          "repairs": {
            "invalid_location_data": {
              "title": "Invalid Location Configuration",
              "description": "The Jewish Calendar integration failed to initialize due to an issue with the configured location data (latitude, longitude, elevation, or timezone).\n\nError: `{error_message}`\n\nPlease reconfigure the integration with valid location settings."
            }
          }
        }
        ```

2.  **Handle Astral Calculation Failures during Sensor Updates:**
    Modify `sensor.py` to create/delete a repair issue when `get_astral_event_date` fails or succeeds.

    *   Import `issue_registry`:
        ```python
        from homeassistant.helpers import issue_registry as ir
        ```
    *   In `JewishCalendarBaseSensor.async_update_data`:
        ```python
        # sensor.py
        # In class JewishCalendarBaseSensor
        async def async_update_data(self) -> None:
            # ... (existing code before event_date) ...
            event_date = get_astral_event_date(self.hass, SUN_EVENT_SUNSET, today)

            if event_date is None:
                _LOGGER.error(
                    "Cannot calculate sunset for date %s, Jewish Calendar sensors may be inaccurate. "
                    "Please check Home Assistant location settings and the integration's location configuration.",
                    today
                )
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "astral_calculation_failed",
                    is_fixable=True,
                    issue_domain=DOMAIN,
                    severity=ir.IssueSeverity.WARNING, # Or ERROR
                    translation_key="astral_calculation_failed",
                    translation_placeholders={"date": str(today)},
                    # learn_more_url: Optional, could point to HA docs on location.
                    config_entry_id=self.config_entry.entry_id,
                )
                # Decide if to return or proceed with partial data if possible.
                # For this example, we'll return as current logic does.
                return
            else:
                # If astral calculations succeed, ensure any existing issue is cleared.
                ir.async_delete_issue(self.hass, DOMAIN, "astral_calculation_failed")

            sunset = dt_util.as_local(event_date)
            # ... (rest of the method) ...
        ```
    *   Add corresponding translation keys to `strings.json`:
        ```json
        // strings.json
        {
          // ... other strings ...
          "repairs": {
            // ... other repair strings ...
            "astral_calculation_failed": {
              "title": "Sunset/Sunrise Calculation Failed",
              "description": "The Jewish Calendar integration could not calculate sunset/sunrise times for `{date}`. This may be due to an invalid or extreme geographic location configured in Home Assistant or for this integration.\n\nPlease verify your location settings to ensure accurate calendar calculations."
            }
          }
        }
        ```

These changes would make the integration more robust by actively informing users of solvable problems and guiding them towards resolution, thereby adhering to the `repair-issues` quality scale rule.

_Created at 2025-05-29 08:32:20. Prompt tokens: 13426, Output tokens: 2080, Total tokens: 20330_
