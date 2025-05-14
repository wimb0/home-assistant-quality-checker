# openweathermap: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires integrations to check if they can be set up correctly during initialization and to raise specific exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) to inform the user about the outcome.

This rule applies to the `openweathermap` integration as it involves communication with a cloud API (`pyopenweathermap`) which can fail due to various reasons, including authentication issues or temporary network problems.

The `openweathermap` integration partially follows this rule by using a `DataUpdateCoordinator` and calling `await weather_coordinator.async_config_entry_first_refresh()` within its `async_setup_entry` function (`__init__.py`):

```python
# homeassistant/components/openweathermap/__init__.py
# ...
    weather_coordinator = WeatherUpdateCoordinator(hass, entry, owm_client)

    await weather_coordinator.async_config_entry_first_refresh() # L35
# ...
```

The `WeatherUpdateCoordinator`'s `_async_update_data` method handles API calls:
```python
# homeassistant/components/openweathermap/coordinator.py
# ...
    async def _async_update_data(self):
        """Update the data."""
        try:
            weather_report = await self._owm_client.get_weather( # L73
                self._latitude, self._longitude
            )
        except RequestError as error: # L76
            raise UpdateFailed(error) from error # L77
        return self._convert_weather_response(weather_report)
# ...
```
If `self._owm_client.get_weather()` raises a `pyopenweathermap.RequestError`, the coordinator re-raises it as `UpdateFailed`. When `async_config_entry_first_refresh()` propagates an `UpdateFailed` exception, Home Assistant typically treats this as a temporary issue, leading to the config entry being marked for retry (similar to raising `ConfigEntryNotReady`). This correctly handles temporary failures like network issues.

However, the integration does not fully comply with the rule because it doesn't differentiate authentication failures (e.g., an invalid API key) to raise `ConfigEntryAuthFailed`. If `pyopenweathermap.RequestError` is due to an invalid API key (e.g., HTTP 401 error), the current implementation will still raise `UpdateFailed`. This results in repeated retries rather than prompting the user for re-authentication, which is the behavior expected when `ConfigEntryAuthFailed` is raised.

The integration should inspect the nature of `pyopenweathermap.RequestError` to determine if it's an authentication issue. If so, `ConfigEntryAuthFailed` should be raised. For other transient errors, `UpdateFailed` (leading to `ConfigEntryNotReady` behavior) is appropriate.

## Suggestions

To fully comply with the `test-before-setup` rule, the `WeatherUpdateCoordinator` should be modified to distinguish authentication errors from other API errors and raise `ConfigEntryAuthFailed` accordingly.

**Modify `homeassistant/components/openweathermap/coordinator.py`:**

Update the `_async_update_data` method in `WeatherUpdateCoordinator` to inspect the `RequestError` from `pyopenweathermap` and raise `ConfigEntryAuthFailed` if the error indicates an authentication problem (e.g., HTTP status code 401, which OpenWeatherMap typically uses for invalid API keys).

```python
# homeassistant/components/openweathermap/coordinator.py

# ... other imports
from pyopenweathermap import (
    # ...
    RequestError,
    # ...
)
# ...
from homeassistant.exceptions import ConfigEntryAuthFailed # Add this import
# ...

class WeatherUpdateCoordinator(DataUpdateCoordinator):
    # ...

    async def _async_update_data(self):
        """Update the data."""
        try:
            weather_report = await self._owm_client.get_weather(
                self._latitude, self._longitude
            )
        except RequestError as error:
            # Assuming pyopenweathermap.RequestError has an attribute like 'status_code'
            # or some other way to identify the nature of the error.
            # The actual attribute and value for an auth error (e.g., 401)
            # from pyopenweathermap needs to be confirmed.
            # For demonstration, let's assume 'error.status' holds the HTTP status code.
            # A common status code for unauthorized/invalid API key is 401.
            if hasattr(error, "status") and error.status == 401:
                _LOGGER.error("Authentication failed with OpenWeatherMap API: %s", error)
                raise ConfigEntryAuthFailed("Invalid API key") from error
            
            # For other API errors (network issues, temporary service unavailability, etc.)
            _LOGGER.warning("Request to OpenWeatherMap API failed: %s", error)
            raise UpdateFailed(f"Error communicating with OpenWeatherMap API: {error}") from error
        return self._convert_weather_response(weather_report)

    # ...
```

**Explanation of Changes:**

1.  **Import `ConfigEntryAuthFailed`**: Add `from homeassistant.exceptions import ConfigEntryAuthFailed`.
2.  **Inspect `RequestError`**: Inside the `except RequestError as error:` block, add logic to check if `error` signifies an authentication failure. This typically involves checking an attribute of the error object that might contain an HTTP status code (e.g., `error.status == 401`). The exact way to determine this depends on the `pyopenweathermap` library's `RequestError` structure.
3.  **Raise `ConfigEntryAuthFailed`**: If an authentication error is detected, raise `ConfigEntryAuthFailed` with an appropriate message. This will signal Home Assistant to initiate a re-authentication flow for the config entry if one is configured.
4.  **Raise `UpdateFailed` for other errors**: If the `RequestError` is not an authentication error, continue to raise `UpdateFailed`. This exception, when propagated by `async_config_entry_first_refresh`, will lead Home Assistant to treat the setup as not ready and schedule a retry.

By making these changes, the `openweathermap` integration will correctly handle both temporary API issues (leading to retries via `ConfigEntryNotReady` implicitly) and authentication failures (leading to a re-authentication prompt via `ConfigEntryAuthFailed`), thus fully complying with the `test-before-setup` rule.

_Created at 2025-05-14 15:20:31. Prompt tokens: 13868, Output tokens: 1541, Total tokens: 22205_
