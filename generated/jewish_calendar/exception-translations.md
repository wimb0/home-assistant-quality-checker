# jewish_calendar: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `exception-translations` rule requires that error messages shown to the user, typically via `HomeAssistantError` or its subclasses, are translatable. This involves raising such exceptions with a `translation_domain` and `translation_key`, and defining the corresponding error messages in the integration's `strings.json` file under an `exceptions` block.

This rule applies to the `jewish_calendar` integration because it provides services and performs operations that can encounter errors, and it is desirable for these error messages to be understood by users in their preferred language.

The integration partially follows this rule:
1.  **Correct Implementation:** In `service.py`, the `is_after_sunset` helper function correctly raises a translatable `HomeAssistantError` if it cannot determine the sunset event date:
    ```python
    # homeassistant/components/jewish_calendar/service.py
    if event_date is None:
        _LOGGER.error("Can't get sunset event date for %s", today)
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="sunset_event"
        )
    ```
    And the corresponding translation is defined in `strings.json`:
    ```json
    // homeassistant/components/jewish_calendar/strings.json
    {
        "exceptions": {
            "sunset_event": {
                "message": "Sunset event cannot be calculated for the provided date and location"
            }
        }
    }
    ```
    This is a good example of adhering to the rule.

2.  **Missing Implementation:** However, the `get_omer_count` service in `service.py` calls methods from the `hdate` library (e.g., `HebrewDate.from_gdate()`, `Omer()`) which can raise exceptions like `hdate.omer.OmerError` (a subclass of `ValueError`) or other `ValueError`s for invalid dates/conditions. These exceptions are not currently caught and re-raised as translatable `HomeAssistantError`s. If such an `hdate` library exception occurs, the user will see the original Python exception message, which is not translatable and may not be user-friendly.
    For example, if `Omer()` is called with a date outside the Omer period, it raises `OmerError` with a message like "Omer can only be counted between Pesach and Shavuot." This message is in English and not managed by Home Assistant's translation system.

    ```python
    # homeassistant/components/jewish_calendar/service.py
    async def get_omer_count(call: ServiceCall) -> ServiceResponse:
        # ...
        hebrew_date = HebrewDate.from_gdate( # This can raise ValueError
            date + datetime.timedelta(days=int(after_sunset))
        )
        # ...
        omer = Omer(date=hebrew_date, nusach=nusach) # This can raise OmerError
        # ...
    ```
    These potential library exceptions are not wrapped, meaning their messages are not translatable through the Home Assistant framework.

Therefore, while the integration demonstrates an understanding of the principle in one case, it does not apply it consistently to all relevant error scenarios, particularly those originating from its dependency library during service calls.

## Suggestions

To make the `jewish_calendar` integration fully compliant with the `exception-translations` rule, you should catch specific exceptions from the `hdate` library in service calls and re-raise them as translatable `HomeAssistantError`s.

1.  **Modify `get_omer_count` service in `service.py`:**
    Wrap calls to `HebrewDate.from_gdate()` and `Omer()` in `try...except` blocks.
    Catch relevant exceptions (e.g., `hdate.omer.OmerError`, `ValueError` from `hdate`'s context) and re-raise them using `HomeAssistantError` with appropriate `translation_key`s.

    **Example Code Change in `homeassistant/components/jewish_calendar/service.py`:**
    ```python
    from hdate import HebrewDate, HDateError  # Add HDateError if it's a relevant base
    from hdate.omer import Nusach, Omer, OmerError # Ensure OmerError is imported
    # ... other imports

    async def get_omer_count(call: ServiceCall) -> ServiceResponse:
        """Return the Omer blessing for a given date."""
        date_input = call.data.get(ATTR_DATE, dt_util.now().date())
        after_sunset = (
            call.data[ATTR_AFTER_SUNSET]
            if ATTR_DATE in call.data
            else is_after_sunset(hass) # This already handles its own potential error
        )

        try:
            hebrew_date_gregorian_arg = date_input + datetime.timedelta(days=int(after_sunset))
            hebrew_date = HebrewDate.from_gdate(hebrew_date_gregorian_arg)
        except ValueError as err: # Catch specific ValueError from hdate if possible, or broader
            _LOGGER.error("Error converting date for Omer count: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="omer_invalid_date_conversion",
                translation_placeholders={"error": str(err)},
            ) from err

        nusach = Nusach[call.data[ATTR_NUSACH].upper()]
        set_language(call.data[CONF_LANGUAGE])

        try:
            omer = Omer(date=hebrew_date, nusach=nusach)
        except OmerError as err:
            _LOGGER.info("Omer counting error: %s", err) # Info level as it's a user input error
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="omer_error_out_of_range",
                # The original message from OmerError is quite clear,
                # but for consistency, we provide a translatable one.
                # translation_placeholders={"original_message": str(err)}, # Optional
            ) from err
        # Potentially catch other HDateError or general ValueError if they are expected from Omer()
        # except HDateError as err: # Broader hdate error
        #     _LOGGER.error("Unexpected hdate error during Omer calculation: %s", err)
        #     raise HomeAssistantError(
        #         translation_domain=DOMAIN,
        #         translation_key="omer_generic_hdate_error",
        #         translation_placeholders={"error": str(err)},
        #     ) from err

        return {
            "message": str(omer.count_str()),
            "weeks": omer.week,
            "days": omer.day,
            "total_days": omer.total_days,
        }
    ```

2.  **Add new translation keys to `strings.json`:**
    Update `homeassistant/components/jewish_calendar/strings.json` to include messages for the new exception keys.

    **Example `strings.json` additions:**
    ```json
    {
      "common": {
        // ... existing common strings
      },
      "entity": {
        // ... existing entity strings
      },
      // ... other existing sections
      "exceptions": {
        "sunset_event": {
          "message": "Sunset event cannot be calculated for the provided date and location"
        },
        "omer_error_out_of_range": {
          "message": "The Omer can only be counted for dates between Pesach and Shavuot."
        },
        "omer_invalid_date_conversion": {
          "message": "The provided date for Omer counting could not be processed: {error}"
        },
        "omer_generic_hdate_error": {
          "message": "An unexpected calendar calculation error occurred while determining the Omer count: {error}"
        }
        // Add other keys as needed for other caught exceptions
      }
    }
    ```

**Why these changes satisfy the rule:**
*   By catching specific library exceptions (like `OmerError` or `ValueError` from `hdate` operations) and re-raising them as `HomeAssistantError` with `translation_domain` and `translation_key`, any error messages presented to the user resulting from these conditions will be translatable.
*   This ensures a more consistent and user-friendly experience for users in different locales, as critical error information will be available in their configured language.
*   It aligns the integration's error handling with Home Assistant's best practices for internationalization.

_Created at 2025-05-29 08:28:40. Prompt tokens: 13518, Output tokens: 2071, Total tokens: 21476_
