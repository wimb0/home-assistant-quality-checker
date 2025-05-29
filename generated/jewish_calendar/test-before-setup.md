# jewish_calendar: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires that integrations check during their initialization (`async_setup_entry`) if they can be set up correctly, and if not, they should raise specific Home Assistant exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) to inform the user.

This rule **applies** to the `jewish_calendar` integration. The `async_setup_entry` function in `homeassistant/components/jewish_calendar/__init__.py` performs a critical initialization step by creating an `hdate.Location` object:

```python
# homeassistant/components/jewish_calendar/__init__.py
# ...
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
# ...
```

This call to instantiate `hdate.Location` (which uses data from the config entry and Home Assistant's configuration) could potentially fail if, for example, an invalid timezone string or other malformed location data is provided. Such a failure would currently lead to an unhandled exception during setup.

The integration currently does **not follow** this rule because the aforementioned call to `hdate.Location` via `hass.async_add_executor_job` is not wrapped in a `try...except` block that would catch potential exceptions (e.g., `ValueError`, `TypeError`, or `zoneinfo.ZoneInfoNotFoundError` from timezone processing) and translate them into `ConfigEntryError`. The integration does not use a data update coordinator, so the implicit handling via `coordinator.async_config_entry_first_refresh()` is not applicable.

If the `Location` object cannot be initialized, the integration cannot function correctly. By not handling these potential errors as specified by the rule, the user experience is degraded as the setup might fail without a clear, user-friendly error message managed by Home Assistant's config entry system.

## Suggestions

To make the `jewish_calendar` integration compliant with the `test-before-setup` rule, you should modify the `async_setup_entry` function in `homeassistant/components/jewish_calendar/__init__.py` to include error handling around the instantiation of the `hdate.Location` object.

1.  **Import necessary exceptions:**
    Ensure `ConfigEntryError` from `homeassistant.exceptions` is imported. If `hdate.Location` or its underlying libraries (like `zoneinfo`) can raise specific exceptions for invalid timezones (e.g., `zoneinfo.ZoneInfoNotFoundError`), import those as well if not already available.

    ```python
    # homeassistant/components/jewish_calendar/__init__.py
    # ...
    import zoneinfo # Already used in config_flow.py
    from homeassistant.exceptions import ConfigEntryError
    # ...
    ```

2.  **Wrap the `Location` instantiation in a `try...except` block:**
    Catch potential exceptions that `hdate.Location` might raise due to invalid configuration data (e.g., invalid timezone, latitude, longitude, or elevation). Raise `ConfigEntryError` to inform the user that the configuration is invalid and needs to be corrected.

    ```python
    # homeassistant/components/jewish_calendar/__init__.py

    # ... (other imports and constants)
    # from homeassistant.exceptions import ConfigEntryError # Add this import
    # import zoneinfo # Add this import if not already present at the top level

    async def async_setup_entry(
        hass: HomeAssistant, config_entry: JewishCalendarConfigEntry
    ) -> bool:
        """Set up a configuration entry for Jewish calendar."""
        language = config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        diaspora = config_entry.data.get(CONF_DIASPORA, DEFAULT_DIASPORA)
        candle_lighting_offset = config_entry.options.get(
            CONF_CANDLE_LIGHT_MINUTES, DEFAULT_CANDLE_LIGHT
        )
        havdalah_offset = config_entry.options.get(
            CONF_HAVDALAH_OFFSET_MINUTES, DEFAULT_HAVDALAH_OFFSET_MINUTES
        )

        try:
            location_data = {
                "name": hass.config.location_name,
                "diaspora": diaspora,
                "latitude": config_entry.data.get(CONF_LATITUDE, hass.config.latitude),
                "longitude": config_entry.data.get(CONF_LONGITUDE, hass.config.longitude),
                "altitude": config_entry.data.get(CONF_ELEVATION, hass.config.elevation),
                "timezone": config_entry.data.get(CONF_TIME_ZONE, hass.config.time_zone),
            }
            location = await hass.async_add_executor_job(
                partial(
                    Location,
                    **location_data
                )
            )
        except (ValueError, TypeError) as ex:
            # These are common exceptions for invalid parameters.
            # hdate.Location might raise these or more specific ones.
            _LOGGER.error(
                "Failed to initialize Location object with data %s: %s",
                location_data,  # Log the data that caused the error
                ex
            )
            raise ConfigEntryError(
                f"Invalid location parameters provided for Jewish Calendar: {ex}. "
                "Please check your latitude, longitude, elevation, and timezone settings."
            ) from ex
        except zoneinfo.ZoneInfoNotFoundError as ex:
            # Specifically for invalid timezone strings if hdate uses zoneinfo
            _LOGGER.error(
                "Invalid timezone '%s' for Jewish Calendar: %s",
                location_data.get("timezone"),
                ex
            )
            raise ConfigEntryError(
                f"Invalid timezone provided: {location_data.get('timezone')}. "
                "Please select a valid timezone."
            ) from ex
        except Exception as ex:  # Catch any other unexpected errors from Location
            _LOGGER.error(
                "Unexpected error initializing Location object with data %s: %s",
                location_data,
                ex
            )
            raise ConfigEntryError(
                "Failed to set up Jewish Calendar due to an unexpected error "
                f"with location data: {ex}"
            ) from ex

        config_entry.runtime_data = JewishCalendarData(
            language,
            diaspora,
            location,
            candle_lighting_offset,
            havdalah_offset,
        )

        await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

        async def update_listener(
            hass: HomeAssistant, config_entry: JewishCalendarConfigEntry
        ) -> None:
            # Trigger update of states for all platforms
            await hass.config_entries.async_reload(config_entry.entry_id)

        config_entry.async_on_unload(config_entry.add_update_listener(update_listener))
        return True
    ```

**Why these changes satisfy the rule:**
By implementing this `try...except` block, if the `hdate.Location` constructor fails due to invalid configuration data (which would prevent the integration from working correctly), a `ConfigEntryError` will be raised. This signals to Home Assistant that the setup failed due to a persistent configuration issue. Home Assistant will then display an appropriate error message to the user in the UI, guiding them to correct the configuration, thus improving the user experience as intended by the `test-before-setup` rule. Logging the error with `_LOGGER.error` also helps in debugging.

_Created at 2025-05-29 08:11:25. Prompt tokens: 13519, Output tokens: 1950, Total tokens: 19546_
