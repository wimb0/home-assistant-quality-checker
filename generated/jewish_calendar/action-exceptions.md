# jewish_calendar: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `action-exceptions` rule applies to the `jewish_calendar` integration because it defines a service, `count_omer`. The rule requires that service actions raise specific Home Assistant exceptions (`ServiceValidationError` or `HomeAssistantError`) when failures are encountered.

The integration partially follows this rule:
1.  The service `count_omer` is defined in `service.py` and registered in `async_setup_services`.
2.  The service handler `get_omer_count` calls a helper function `is_after_sunset`. This helper function correctly checks for a potential failure condition (when `get_astral_event_date` returns `None`) and raises a `HomeAssistantError` with a translation key, as seen in `service.py`:
    ```python
    # homeassistant/components/jewish_calendar/service.py
    def is_after_sunset(hass: HomeAssistant) -> bool:
        # ...
        if event_date is None:
            _LOGGER.error("Can't get sunset event date for %s", today)
            raise HomeAssistantError(  # Correctly raises HomeAssistantError
                translation_domain=DOMAIN, translation_key="sunset_event"
            )
        # ...
    ```
3.  Input validation for the `count_omer` service is handled by a `voluptuous` schema (`OMER_SCHEMA`). If this validation fails, Home Assistant typically raises an error before the service handler is called. This generally covers the `ServiceValidationError` aspect for malformed direct input.

However, the integration does not fully follow the rule because the main logic within the `get_omer_count` service handler, which involves calls to the `hdate` library, does not explicitly catch potential exceptions from this library and wrap them in `HomeAssistantError`.
Specifically, these calls in `service.py`:
```python
# homeassistant/components/jewish_calendar/service.py
async def get_omer_count(call: ServiceCall) -> ServiceResponse:
    # ...
    hebrew_date = HebrewDate.from_gdate(
        date + datetime.timedelta(days=int(after_sunset))
    )
    nusach = Nusach[call.data[ATTR_NUSACH].upper()]
    set_language(call.data[CONF_LANGUAGE])
    omer = Omer(date=hebrew_date, nusach=nusach)
    return {
        "message": str(omer.count_str()),
        # ...
    }
```
If any of these `hdate` library calls (e.g., `HebrewDate.from_gdate()`, `Omer()`, `omer.count_str()`) raise an unexpected Python exception (e.g., `ValueError`, `TypeError`, or a custom `hdate` library exception not derived from `HomeAssistantError`), this exception will propagate uncaught by the integration's specific error handling for services. The rule requires that such internal errors be raised as `HomeAssistantError`.

## Suggestions

To make the `jewish_calendar` integration compliant with the `action-exceptions` rule, you should modify the `get_omer_count` service handler in `homeassistant/components/jewish_calendar/service.py` to catch potential exceptions from the `hdate` library calls and re-raise them as `HomeAssistantError`.

Here's how you can modify the `get_omer_count` function:

```python
# homeassistant/components/jewish_calendar/service.py

import datetime
import logging
from typing import get_args

from hdate import HebrewDate
# Consider importing a base exception from hdate if available, e.g., from hdate.exceptions import HDateError
from hdate.omer import Nusach, Omer
from hdate.translator import Language, set_language
import voluptuous as vol

from homeassistant.const import CONF_LANGUAGE, SUN_EVENT_SUNSET
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError # Ensure this is imported
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import LanguageSelector, LanguageSelectorConfig
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util import dt as dt_util

from .const import ATTR_AFTER_SUNSET, ATTR_DATE, ATTR_NUSACH, DOMAIN, SERVICE_COUNT_OMER

_LOGGER = logging.getLogger(__name__)
OMER_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DATE): cv.date,
        vol.Optional(ATTR_AFTER_SUNSET, default=True): cv.boolean,
        vol.Required(ATTR_NUSACH, default="sfarad"): vol.In(
            [nusach.name.lower() for nusach in Nusach]
        ),
        vol.Optional(CONF_LANGUAGE, default="he"): LanguageSelector(
            LanguageSelectorConfig(languages=list(get_args(Language)))
        ),
    }
)


def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the Jewish Calendar services."""

    # is_after_sunset function remains the same

    def is_after_sunset(hass: HomeAssistant) -> bool:
        """Determine if the current time is after sunset."""
        now = dt_util.now()
        today = now.date()
        event_date = get_astral_event_date(hass, SUN_EVENT_SUNSET, today)
        if event_date is None:
            _LOGGER.error("Can't get sunset event date for %s", today)
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="sunset_event"
            )
        sunset = dt_util.as_local(event_date)
        _LOGGER.debug("Now: %s Sunset: %s", now, sunset)
        return now > sunset

    async def get_omer_count(call: ServiceCall) -> ServiceResponse:
        """Return the Omer blessing for a given date."""
        date_input = call.data.get(ATTR_DATE, dt_util.now().date())
        after_sunset_input = (
            call.data[ATTR_AFTER_SUNSET]
            if ATTR_DATE in call.data
            else is_after_sunset(hass) # This already raises HomeAssistantError if needed
        )
        
        try:
            hebrew_date = HebrewDate.from_gdate(
                date_input + datetime.timedelta(days=int(after_sunset_input))
            )
            # The schema validation should prevent invalid nusach values from reaching here.
            # If it could still fail, this might also need a more specific error or check.
            nusach = Nusach[call.data[ATTR_NUSACH].upper()]
            set_language(call.data[CONF_LANGUAGE])
            omer = Omer(date=hebrew_date, nusach=nusach)
            message = str(omer.count_str())
            
            return {
                "message": message,
                "weeks": omer.week,
                "days": omer.day,
                "total_days": omer.total_days,
            }
        # It's good practice to catch more specific exceptions if known from the hdate library.
        # For example, if hdate has its own base exception (e.g., HDateError).
        # Catching (ValueError, TypeError) is a common fallback for unexpected library issues.
        except (ValueError, TypeError, KeyError, AttributeError) as err: # Add other relevant hdate specific exceptions if any
            _LOGGER.error("Error calculating Omer count using hdate library: %s", err)
            # It's better to use a translation key if a generic "calculation_failed" message is suitable
            raise HomeAssistantError(
                f"Failed to calculate Omer count due to an internal error: {err}"
            ) from err
        except Exception as err:  # Catch any other unexpected exception
            _LOGGER.exception("Unexpected error calculating Omer count: %s", err)
            # It's better to use a translation key for a generic "unexpected_error" message
            raise HomeAssistantError(
                "An unexpected error occurred while calculating the Omer count."
            ) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_COUNT_OMER,
        get_omer_count,
        schema=OMER_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

```

**Why these changes satisfy the rule:**

*   The `try...except` block now wraps the critical section of code that interacts with the `hdate` library.
*   If `hdate` calls raise exceptions like `ValueError`, `TypeError`, `KeyError`, `AttributeError` (or more specific `hdate` exceptions if they exist and are caught), these are caught.
*   These caught exceptions are then re-raised as `HomeAssistantError`. This ensures that if the service action fails due to an issue within its own processing (including issues from underlying libraries), it explicitly signals this failure using the correct Home Assistant exception type.
*   A final `except Exception` can catch any other unforeseen errors and also wrap them in a `HomeAssistantError`, providing a robust error handling mechanism.
*   This change aligns with the rule's requirement to "raise an exception to indicate that something went wrong" and specifically to "raise a `HomeAssistantError`" when "the problem is caused by an error in the service action itself".

_Created at 2025-05-29 08:13:00. Prompt tokens: 13460, Output tokens: 2306, Total tokens: 19438_
