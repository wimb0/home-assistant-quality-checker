# jewish_calendar: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `action-setup` rule requires that service actions are registered in the `async_setup` method and that they validate whether any required configuration entry is loaded, raising a `ServiceValidationError` if not.

This rule applies to the `jewish_calendar` integration as it provides a service (`count_omer`).

The integration partially follows the rule:
1.  **Service Registration:** The `count_omer` service is registered via the `async_setup_services` function, which is called from `async_setup` in `homeassistant/components/jewish_calendar/__init__.py` (L32-L35). This correctly places service registration within `async_setup`.

    ```python
    # homeassistant/components/jewish_calendar/__init__.py
    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up the Jewish Calendar service."""
        async_setup_services(hass) # Service registration initiated here
        return True
    ```

    ```python
    # homeassistant/components/jewish_calendar/service.py
    def async_setup_services(hass: HomeAssistant) -> None:
        """Set up the Jewish Calendar services."""
        # ...
        hass.services.async_register( # Actual registration
            DOMAIN,
            SERVICE_COUNT_OMER,
            get_omer_count,
            schema=OMER_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )
    ```

2.  **Config Entry Dependency and Validation:** The integration does **not** fully follow this aspect. The `count_omer` service (defined in `service.py`) has a behavior that depends on location settings when the optional `ATTR_DATE` parameter is not provided. In this default case, it needs to determine if the current time is after sunset to correctly calculate the Hebrew date.
    *   Currently, the `is_after_sunset` helper function (L38-L49 in `service.py`), used by `get_omer_count` (L55), relies on global Home Assistant location settings (`get_astral_event_date(hass, ...)` which uses `hass.config.latitude/longitude`).
    *   The `jewish_calendar` integration, however, can be configured with a specific location (`latitude`, `longitude`, `elevation`, `time_zone`) via its config entry (see `__init__.py::async_setup_entry`). This specific location can differ from the global HA settings and is stored in `config_entry.runtime_data.location`.
    *   The `count_omer` service does not currently attempt to use this entry-specific location for its default sunset calculation.
    *   Crucially, it does not check if the `jewish_calendar` config entry exists or is loaded (`ConfigEntryState.LOADED`) before performing calculations that should ideally use the entry's configured settings. If the entry is not loaded, `runtime_data` (including the specific `Location` object) would not be available. The rule requires raising `ServiceValidationError` in such scenarios.

    The `manifest.json` specifies `"single_config_entry": true`, meaning there will be at most one configuration entry for this integration. The service should, therefore, attempt to use this single entry's data.

## Suggestions

To make the `jewish_calendar` integration compliant with the `action-setup` rule, the `get_omer_count` service handler in `homeassistant/components/jewish_calendar/service.py` needs to be modified to correctly use the integration's configured location data and validate the config entry's state.

1.  **Import necessary modules** in `homeassistant/components/jewish_calendar/service.py`:
    ```python
    from hdate import Zmanim # Add Zmanim
    # ...
    from homeassistant.config_entries import ConfigEntryState # Add ConfigEntryState
    from homeassistant.exceptions import ServiceValidationError, HomeAssistantError # Add ServiceValidationError
    # ...
    from .entity import JewishCalendarData # Add JewishCalendarData for type hinting
    ```

2.  **Modify the `get_omer_count` service handler:**
    When `ATTR_DATE` is not provided in the service call, the service should:
    *   Fetch the `jewish_calendar` config entry.
    *   If the entry is not found, raise a `ServiceValidationError`.
    *   Check if the entry's state is `ConfigEntryState.LOADED`. If not, raise a `ServiceValidationError`.
    *   Use the `location` (and potentially other relevant data like offsets) from `entry.runtime_data` to calculate sunset for the current day. The `hdate.Zmanim` class is suitable for this, ensuring consistency with how entities in the integration might calculate times.
    *   Compare the current time with this calculated sunset to determine if it's "after sunset."

    Here's an example of how `get_omer_count` could be refactored:

    ```python
    # homeassistant/components/jewish_calendar/service.py

    # ... (imports) ...
    # The existing is_after_sunset helper might become obsolete for this service's default path,
    # or be refactored if still needed elsewhere with global HA settings.

    async def get_omer_count(call: ServiceCall) -> ServiceResponse:
        """Return the Omer blessing for a given date."""
        current_gregorian_date = call.data.get(ATTR_DATE, dt_util.now().date())

        is_past_sunset: bool
        if ATTR_DATE in call.data:
            # User provided a date, so use the explicitly provided after_sunset flag
            is_past_sunset = call.data[ATTR_AFTER_SUNSET]
        else:
            # No date provided by user, calculate after_sunset based on current time and configured location
            now = dt_util.now()
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                raise ServiceValidationError(
                    "Jewish Calendar config entry not found. Please configure the integration first.",
                    translation_domain=DOMAIN,
                    translation_key="config_entry_not_found_for_service" # Ensure this key exists in strings.json
                )

            entry = entries[0] # single_config_entry: true
            if entry.state is not ConfigEntryState.LOADED:
                raise ServiceValidationError(
                    f"Jewish Calendar config entry '{entry.title}' is not loaded. The service cannot determine sunset time.",
                    translation_domain=DOMAIN,
                    translation_key="config_entry_not_loaded_for_service", # Ensure this key exists
                    translation_placeholders={"entry_title": entry.title}
                )

            calendar_data: JewishCalendarData = entry.runtime_data

            try:
                # Use hdate.Zmanim with the entry's specific location and offsets
                zmanim_for_sunset_calc = Zmanim(
                    date=now.date(), # Use current date for this calculation
                    location=calendar_data.location,
                    candle_lighting_offset=calendar_data.candle_lighting_offset,
                    havdalah_offset=calendar_data.havdalah_offset
                )
                # 'shkia' is the key for sunset in hdate.Zmanim.zmanim
                sunset_datetime = zmanim_for_sunset_calc.zmanim["shkia"].local
                if sunset_datetime is None:
                    # This case should ideally be caught by Zmanim or location validation earlier,
                    # but as a safeguard:
                    raise ValueError("Sunset time could not be determined.")
            except Exception as e: # Catch potential errors from Zmanim instantiation or access
                _LOGGER.error("Error calculating sunset for Omer service using configured location: %s", e)
                raise ServiceValidationError(
                    "Failed to calculate sunset time using the configured location for the Jewish Calendar integration.",
                    translation_domain=DOMAIN,
                    translation_key="sunset_error_for_service" # Ensure this key exists
                ) from e

            is_past_sunset = now > sunset_datetime

        # Determine the Hebrew date based on the Gregorian date and whether it's past sunset
        hebrew_date_base = current_gregorian_date
        if is_past_sunset:
            hebrew_date_base += datetime.timedelta(days=1)

        hebrew_date_obj = HebrewDate.from_gdate(hebrew_date_base)
        nusach = Nusach[call.data[ATTR_NUSACH].upper()]
        set_language(call.data[CONF_LANGUAGE]) # Ensure set_language is thread-safe if services run concurrently
        omer = Omer(date=hebrew_date_obj, nusach=nusach)

        return {
            "message": str(omer.count_str()),
            "weeks": omer.week,
            "days": omer.day,
            "total_days": omer.total_days,
        }

    # ... (rest of async_setup_services, ensure hass.services.async_register uses the modified get_omer_count)
    ```

3.  **Add Translations:** Ensure that any new translation keys used in `ServiceValidationError` (e.g., `config_entry_not_found_for_service`, `config_entry_not_loaded_for_service`, `sunset_error_for_service`) are added to `homeassistant/components/jewish_calendar/strings.json` under an appropriate section (e.g., a new `exceptions` sub-key for services or using existing ones if applicable).

**Why these changes satisfy the rule:**
*   The service will explicitly check for the existence and loaded state of its configuration entry when its default behavior relies on data from that entry.
*   It will raise `ServiceValidationError` with user-friendly (translatable) messages if the entry is not found or not loaded, allowing users to understand why the service call failed.
*   The service's behavior will be consistent with the rest of the integration by using the same configured location data for its calculations.

---

_Created at 2025-05-29 10:25:00. Prompt tokens: 13584, Output tokens: 2420, Total tokens: 23561_
_Report based on [`8018949`](https://github.com/home-assistant/core/tree/80189495c54cbf795270c99019898bc831555703)_

_AI can be wrong. Always verify the report and the code against the rule._
