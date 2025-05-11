# home_connect: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires that an integration, during its initialization phase (`async_setup_entry`), checks if it can be set up correctly. This involves attempting to connect to the device or service and handling potential errors by raising specific exceptions: `ConfigEntryNotReady` for temporary issues, `ConfigEntryAuthFailed` for authentication problems, and `ConfigEntryError` for permanent, non-authentication failures.

The `home_connect` integration adheres to this rule through a combination of checks in `__init__.py` and its `HomeConnectCoordinator`.

1.  **Initial Authentication Check (`__init__.py`)**:
    In `async_setup_entry` within `home_connect/__init__.py`, the integration first attempts to obtain an access token:
    ```python
    # home_connect/__init__.py
    config_entry_auth = AsyncConfigEntryAuth(hass, session)
    try:
        await config_entry_auth.async_get_access_token()
    except aiohttp.ClientResponseError as err:
        if 400 <= err.status < 500: # Covers authentication issues (e.g., 401, 403)
            raise ConfigEntryAuthFailed from err
        raise ConfigEntryNotReady from err # Covers other client response errors (e.g., server down)
    except aiohttp.ClientError as err: # Covers general client errors (e.g., connection refused)
        raise ConfigEntryNotReady from err
    ```
    This block correctly raises `ConfigEntryAuthFailed` for HTTP client errors typically associated with authentication (status codes 400-499) and `ConfigEntryNotReady` for other client response errors or general client errors, which are likely temporary.

2.  **Coordinator-Based Setup and API Interaction (`coordinator.py`)**:
    After successful token acquisition, `async_setup_entry` initializes `HomeConnectCoordinator` and calls `await coordinator.async_setup()`. This method, defined in `home_connect/coordinator.py`, performs the initial API calls to fetch appliance data:
    ```python
    # home_connect/coordinator.py
    async def async_setup(self) -> None:
        """Set up the devices."""
        try:
            await self._async_setup()
        except UpdateFailed as err:
            raise ConfigEntryNotReady from err

    async def _async_setup(self) -> None:
        """Set up the devices."""
        # ...
        try:
            appliances = await self.client.get_home_appliances() # Initial API call
        except UnauthorizedError as error: # Specific aiohomeconnect auth error
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_error",
                translation_placeholders=get_dict_from_home_connect_error(error),
            ) from error
        except HomeConnectError as error: # General aiohomeconnect error
            # ...
            raise UpdateFailed( # This becomes ConfigEntryNotReady
                translation_domain=DOMAIN,
                translation_key="fetch_api_error",
                translation_placeholders=get_dict_from_home_connect_error(error),
            ) from error
        # ...
    ```
    Here, `_async_setup` (called by `async_setup`) makes an API call to `get_home_appliances`.
    *   If an `UnauthorizedError` (from the `aiohomeconnect` library) occurs, it correctly raises `ConfigEntryAuthFailed`.
    *   For other `HomeConnectError` instances, it raises `UpdateFailed`. The calling `async_setup` method catches this `UpdateFailed` and re-raises it as `ConfigEntryNotReady`. This is appropriate for general API errors that might be temporary.

This two-stage approach ensures that both OAuth token validity and basic API communication (fetching initial appliance list) are verified before `async_setup_entry` successfully completes. If any of these initial checks fail, the appropriate `ConfigEntryAuthFailed` or `ConfigEntryNotReady` exception is raised, preventing the integration from loading incorrectly and informing the user or prompting Home Assistant to retry.

While the integration does not explicitly raise `ConfigEntryError` for a permanent non-authentication failure (e.g., "account closed"), this is often difficult to determine robustly from the client-side without specific API error codes. The current handling of raising `ConfigEntryNotReady` for most non-auth API errors is a reasonable default, as it allows for retries.

The implementation aligns with the rule's intent and examples, including the implicit handling via a data update coordinator's initial setup/refresh mechanism.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 20:31:25. Prompt tokens: 139380, Output tokens: 1167, Total tokens: 144456_
