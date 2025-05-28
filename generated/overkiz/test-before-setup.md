# overkiz: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires that integrations check during their initialization if they can be set up correctly, and to inform the user about failures by raising appropriate `ConfigEntry` exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`).

This rule applies to the `overkiz` integration as it communicates with external hardware or cloud services that can be unavailable or misconfigured.

The `overkiz` integration partially follows this rule. In its `async_setup_entry` function (in `homeassistant/components/overkiz/__init__.py`), it correctly performs initial API calls to test the connection and authentication before fully setting up the integration:
1.  `await client.login()`: Tests authentication and basic connectivity.
2.  `await client.get_setup()`: Tests the ability to fetch the initial device configuration.
3.  `await client.get_scenarios()` (for cloud API): Tests the ability to fetch scenarios.

These calls are wrapped in a `try...except` block that handles several common exceptions from the `pyoverkiz` library and `aiohttp`:
*   `BadCredentialsException`, `NotSuchTokenException`, `NotAuthenticatedException` are correctly mapped to `ConfigEntryAuthFailed`.
*   `TooManyRequestsException` (from `pyoverkiz`), `TimeoutError`, `ClientError` (from `aiohttp`), and `MaintenanceException` (from `pyoverkiz`) are correctly mapped to `ConfigEntryNotReady`.

However, the integration does not fully follow the rule because the `try...except` block in `async_setup_entry` for these initial calls is not exhaustive for all relevant known exceptions from the `pyoverkiz` library. Specifically:

*   **`pyoverkiz.exceptions.TooManyAttemptsBannedException`**: This exception can be raised by `client.login()` if the API temporarily bans the client due to too many failed attempts. This exception is not caught in the `async_setup_entry` function's initial `try...except` block (lines 75-93 in `homeassistant/components/overkiz/__init__.py`). If raised by the initial `client.login()`, `client.get_setup()`, or `client.get_scenarios()` calls, it would result in an unhandled exception, leading to a generic setup failure rather than a graceful `ConfigEntryNotReady`.

While the `OverkizDataUpdateCoordinator` (used later via `coordinator.async_config_entry_first_refresh()`) has more extensive exception handling, this does not cover the very first `login`, `get_setup`, and `get_scenarios` calls made directly within `async_setup_entry` *before* the coordinator's first refresh. The rule applies to these initial critical checks.

Additionally, the integration does not explicitly raise `ConfigEntryError` for any known permanent, non-authentication errors from `pyoverkiz` during setup. While `pyoverkiz` may not define many such distinct exceptions for the setup phase (most are auth or temporary), if such error types exist or are added, they should be handled.

## Suggestions

To make the `overkiz` integration fully compliant with the `test-before-setup` rule, the following changes are recommended in `homeassistant/components/overkiz/__init__.py`:

1.  **Handle `TooManyAttemptsBannedException`**:
    Modify the `try...except` block in `async_setup_entry` to catch `TooManyAttemptsBannedException` and raise `ConfigEntryNotReady`. This will allow Home Assistant to retry the setup later, which is appropriate for a temporary ban.

    ```python
    # In homeassistant/components/overkiz/__init__.py

    # Add to imports:
    from pyoverkiz.exceptions import (
        BadCredentialsException,
        MaintenanceException,
        NotAuthenticatedException,
        NotSuchTokenException,
        TooManyRequestsException,
        TooManyAttemptsBannedException, # Add this import
    )

    # ...

    async def async_setup_entry(hass: HomeAssistant, entry: OverkizDataConfigEntry) -> bool:
        # ... (client creation) ...

        try:
            await client.login()
            setup = await client.get_setup()

            if api_type == APIType.CLOUD:
                scenarios = await client.get_scenarios()
            else:
                scenarios = []
        except (
            BadCredentialsException,
            NotSuchTokenException,
            NotAuthenticatedException,
        ) as exception:
            raise ConfigEntryAuthFailed("Invalid authentication") from exception
        except TooManyRequestsException as exception:
            raise ConfigEntryNotReady("Too many requests, try again later") from exception
        except (TimeoutError, ClientError) as exception:
            raise ConfigEntryNotReady("Failed to connect") from exception
        except MaintenanceException as exception:
            raise ConfigEntryNotReady("Server is down for maintenance") from exception
        except TooManyAttemptsBannedException as exception:  # Add this block
            raise ConfigEntryNotReady(
                "Too many attempts, API temporarily banned. Will retry later."
            ) from exception
        # Potentially, a more general OverkizException catch here if appropriate for ConfigEntryError
        # except OverkizException as exception:
        #     # Log the error and raise ConfigEntryError if it's a known permanent, non-auth issue
        #     LOGGER.error("Unhandled Overkiz setup error: %s", exception)
        #     raise ConfigEntryError(f"Failed to setup Overkiz hub: {exception}") from exception

        # ... (rest of the function) ...
    ```

2.  **Consider `ConfigEntryError` for other permanent issues (if applicable)**:
    Review if `pyoverkiz.login()`, `pyoverkiz.get_setup()`, or `pyoverkiz.get_scenarios()` can raise other specific `OverkizException` types (not subclasses of already handled ones) that indicate a permanent, non-recoverable, non-authentication error (e.g., a definitively unsupported gateway type reported by the API *after* login). If such exceptions exist or are introduced in `pyoverkiz`, they should be caught and re-raised as `ConfigEntryError`. Currently, there isn't an obvious candidate from `pyoverkiz.exceptions` for this specific handling beyond what's covered by auth or temporary errors.

By implementing suggestion #1, the integration will more robustly handle known temporary failure states during initialization, improving the user experience by allowing automatic retries instead of an unhandled error.

_Created at 2025-05-28 12:15:54. Prompt tokens: 87052, Output tokens: 1590, Total tokens: 95974_
