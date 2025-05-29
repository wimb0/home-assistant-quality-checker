# nest: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `reauthentication-flow` rule requires that integrations using authentication provide a UI-based flow for users to update their credentials if they become invalid, without needing to delete and re-add the integration.

The `nest` integration uses OAuth2 for authentication with Google's Smart Device Management (SDM) API. Therefore, this rule applies.

The integration correctly implements the reauthentication flow:

1.  **Triggering Reauthentication:**
    In `homeassistant/components/nest/__init__.py`, the `async_setup_entry` function makes API calls that can result in authentication errors. If such errors occur (e.g., `ClientResponseError` with a 4xx status or `AuthException`), a `ConfigEntryAuthFailed` exception is raised (lines 179-180, 202-205):
    ```python
    # homeassistant/components/nest/__init__.py
    try:
        await auth.async_get_access_token()
    except ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed from err # Triggers reauth
        raise ConfigEntryNotReady from err
    # ...
    except AuthException as err:
        raise ConfigEntryAuthFailed( # Triggers reauth
            f"Subscriber authentication error: {err!s}"
        ) from err
    ```
    Raising `ConfigEntryAuthFailed` signals Home Assistant to initiate the reauthentication flow for the config entry.

2.  **Config Flow Implementation:**
    The `homeassistant/components/nest/config_flow.py` file contains the `NestFlowHandler`, which inherits from `config_entry_oauth2_flow.AbstractOAuth2FlowHandler`. It implements the necessary methods for reauthentication:

    *   `async_step_reauth(self, entry_data: Mapping[str, Any])`: This method is called by Home Assistant when reauthentication is needed. It stores the existing entry data and transitions to `async_step_reauth_confirm`.
        ```python
        # homeassistant/components/nest/config_flow.py
        async def async_step_reauth(
            self, entry_data: Mapping[str, Any]
        ) -> ConfigFlowResult:
            """Perform reauth upon an API authentication error."""
            _LOGGER.debug("async_step_reauth %s", self.source)
            self._data.update(entry_data)
            return await self.async_step_reauth_confirm()
        ```

    *   `async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None)`: This step displays a form to the user, informing them that reauthentication is required. The UI for this form is defined in `strings.json` under the `reauth_confirm` key.
        ```python
        # homeassistant/components/nest/config_flow.py
        async def async_step_reauth_confirm(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            """Confirm reauth dialog."""
            if user_input is None:
                return self.async_show_form(step_id="reauth_confirm")
            return await self.async_step_user()
        ```
        ```json
        // homeassistant/components/nest/strings.json
        "reauth_confirm": {
            "title": "[%key:common::config_flow::title::reauth%]",
            "description": "The Nest integration needs to re-authenticate your account"
        }
        ```
        Upon confirmation, it proceeds to `async_step_user`.

3.  **OAuth2 Flow and Entry Update:**
    *   In `async_step_user`, if `self.source == SOURCE_REAUTH`, it calls `super().async_step_user(user_input)`. This invokes the `AbstractOAuth2FlowHandler`'s logic to initiate the OAuth2 authorization code flow, redirecting the user to Google to re-authenticate.
    *   After successful re-authentication with Google, the `async_oauth_create_entry` method is called with the new token data.
        ```python
        # homeassistant/components/nest/config_flow.py
        async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
            """Complete OAuth setup and finish pubsub or finish."""
            _LOGGER.debug("Finishing post-oauth configuration")
            self._data.update(data) # data contains the new token
            _LOGGER.debug("self.source=%s", self.source)
            if self.source == SOURCE_REAUTH:
                _LOGGER.debug("Skipping Pub/Sub configuration")
                return await self._async_finish() # Proceed to update the entry
            return await self.async_step_pubsub_topic()
        ```
    *   The `_async_finish` method then updates the existing configuration entry with the new token data and reloads the integration.
        ```python
        # homeassistant/components/nest/config_flow.py
        async def _async_finish(self) -> ConfigFlowResult:
            """Create an entry for the SDM flow."""
            _LOGGER.debug("Creating/updating configuration entry")
            # Update existing config entry when in the reauth flow.
            if self.source == SOURCE_REAUTH:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), # Gets the entry that triggered reauth
                    data=self._data, # Contains the updated token
                )
            # ... (code for initial setup) ...
        ```

This implementation aligns with the requirements of the `reauthentication-flow` rule for an OAuth2-based integration, allowing users to refresh their credentials through the UI without deleting and re-adding the integration.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:00:48. Prompt tokens: 32879, Output tokens: 1456, Total tokens: 38044_
