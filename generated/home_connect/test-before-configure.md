# home_connect: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **todo**                                                                 |

## Overview

The `test-before-configure` rule requires that an integration tests its connection to the device or service during the config flow, before the configuration entry is created. This is to provide immediate feedback to the user if there are issues such as incorrect credentials, network problems, or API errors.

The `home_connect` integration uses OAuth2 for authentication. The current implementation performs connection tests (validating the token and fetching appliance data) within the `async_setup_entry` function (specifically, `config_entry_auth.async_get_access_token()` and `coordinator._async_setup()` which calls `self.client.get_home_appliances()`).

While these tests do occur before the integration's platforms are fully set up and will result in the config entry being marked as `NEEDS_REAUTH` (for `ConfigEntryAuthFailed`) or `SETUP_RETRY`/`SETUP_ERROR` (for `ConfigEntryNotReady`), they happen *after* the config flow UI has completed (typically showing "Success!") and the `ConfigEntry` object itself has been created.

The rule, and its provided example, imply that the connection test should occur *within a method of the `ConfigFlow` handler class* (e.g., `async_step_user` or, for OAuth flows, `async_oauth_create_entry`) *before* the config entry is finalized. This allows the config flow UI to directly show an error to the user (e.g., by returning `self.async_abort(reason="...")`) instead of creating an entry that immediately fails setup.

The `home_connect` integration's `config_flow.py` (`OAuth2FlowHandler.async_oauth_create_entry`) currently does not perform a direct API call to the Home Connect service (like fetching appliances) to test the usability of the acquired token before creating the entry. It decodes the token for the `unique_id` but defers the actual API interaction test to `async_setup_entry`.

Therefore, the integration does not fully follow the `test-before-configure` rule as the test is not performed within the config flow handler in a way that can directly abort the flow with a user-facing error message prior to entry creation.

## Suggestions

To comply with the `test-before-configure` rule, the Home Connect integration should perform a test API call within the `OAuth2FlowHandler.async_oauth_create_entry` method in `config_flow.py`, before the config entry is created.

1.  **Modify `OAuth2FlowHandler.async_oauth_create_entry`:**
    *   After obtaining the token data but before creating the config entry (i.e., before `self.async_create_entry(...)` or `super().async_oauth_create_entry(...)` is called effectively).
    *   Create a temporary authentication mechanism or adapt `AsyncConfigEntryAuth` to use the newly acquired token from the `data` dictionary.
    *   Instantiate `HomeConnectClient` using this auth mechanism.
    *   Perform a test API call, for example, `await client.get_home_appliances()`.
    *   Handle potential exceptions:
        *   If `aiohomeconnect.model.error.UnauthorizedError` occurs, return `self.async_abort(reason="oauth_unauthorized")`. This indicates the token is invalid or the client is not authorized for the API.
        *   If other `aiohomeconnect.model.error.HomeConnectError` or `aiohttp.ClientError` (for network issues) occur, return `self.async_abort(reason="cannot_connect")`. This indicates a general problem communicating with the API.
        *   For any other unexpected exceptions, log the error and return `self.async_abort(reason="unknown")`.
    *   If the test API call is successful, proceed to set the unique ID and create the config entry as currently done.

2.  **Define Error Strings (if new abort reasons are used):**
    *   Ensure that any custom abort reasons used (e.g., if `cannot_connect` is not suitable for all API errors) are defined in `strings.json` under `config.abort` to provide clear error messages to the user. Standard reasons like `oauth_unauthorized`, `cannot_connect`, and `unknown` are generally available.

**Example Snippet for `config_flow.py`:**

```python
# In homeassistant/components/home_connect/config_flow.py
import logging # Ensure logger is available if not already
import aiohttp # For aiohttp.ClientError
import jwt

from aiohomeconnect.client import Client as HomeConnectClient, AbstractAuth
from aiohomeconnect.const import API_ENDPOINT
from aiohomeconnect.model.error import HomeConnectError, UnauthorizedError

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.httpx_client import get_async_client # For the temporary auth

from .const import DOMAIN # Ensure DOMAIN is imported

# ... other imports

_LOGGER = logging.getLogger(__name__) # Define logger for the module


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Home Connect OAuth2 authentication."""

    DOMAIN = DOMAIN
    MINOR_VERSION = 3 # Current minor version

    @property
    def logger(self) -> logging.Logger: # Ensure this property exists or use _LOGGER directly
        """Return logger."""
        return _LOGGER

    # ... (async_step_reauth, async_step_reauth_confirm remain the same) ...

    async def async_oauth_create_entry(self, data: dict) -> ConfigFlowResult:
        """Create an oauth config entry or update existing entry for reauth."""
        user_id_from_token = jwt.decode(
            data["token"]["access_token"], options={"verify_signature": False}
        )["sub"]

        # --- Start of suggested addition for connection test ---
        class _TestAuth(AbstractAuth):
            """Minimal auth class for testing the token during config flow."""
            def __init__(self, hass: HomeAssistant, token_data: dict):
                # Use get_async_client for HTTPX, or aiohttp.ClientSession if aiohomeconnect uses aiohttp directly
                super().__init__(get_async_client(hass), API_ENDPOINT)
                self._token_data = token_data

            async def async_get_access_token(self) -> str:
                return self._token_data["access_token"]

        try:
            self.logger.debug("Attempting to test Home Connect connection with new token.")
            test_auth = _TestAuth(self.hass, data["token"])
            client = HomeConnectClient(auth=test_auth)
            await client.get_home_appliances()  # Test API call
            self.logger.debug("Home Connect connection test successful.")
        except UnauthorizedError as err:
            self.logger.warning("Home Connect API test failed (Unauthorized): %s", err)
            return self.async_abort(reason="oauth_unauthorized")
        except (HomeConnectError, aiohttp.ClientError) as err: # Catch other connection/API errors
            self.logger.error("Home Connect API test failed (Connection/API Error): %s", err)
            return self.async_abort(reason="cannot_connect")
        except Exception:  # noqa: BLE001
            self.logger.exception("Unexpected error during Home Connect API test in config flow")
            return self.async_abort(reason="unknown")
        # --- End of suggested addition ---

        await self.async_set_unique_id(user_id_from_token)

        if self.source == config_entry_oauth2_flow.SOURCE_REAUTH:
            existing_entry = self._get_reauth_entry()
            if not existing_entry or existing_entry.unique_id != user_id_from_token:
                 return self.async_abort(reason="wrong_account")
            
            self.logger.debug("Updating existing Home Connect entry for reauthentication.")
            return self.async_update_reload_and_abort(
                existing_entry, data=data
            )

        self._abort_if_unique_id_configured()
        
        self.logger.debug("Creating new Home Connect config entry.")
        return self.async_create_entry(
            title=self.flow_impl.name,
            data=data,
        )

```

By implementing this, if `client.get_home_appliances()` fails, the config flow will abort and display the relevant error message directly to the user, rather than creating a config entry that subsequently fails. This aligns with the user experience goals of the `test-before-configure` rule.

_Created at 2025-05-10 20:30:23. Prompt tokens: 140003, Output tokens: 2102, Total tokens: 150370_
