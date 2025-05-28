# overkiz: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **done**                                       |
| Reason | N/A |

## Overview

The `reauthentication-flow` rule requires that integrations using authentication provide a UI flow for users to update their credentials if they become invalid, without needing to delete and re-add the integration. This is typically triggered when an API call fails due to an authentication error.

The `overkiz` integration supports two authentication methods:
1.  **Cloud API:** Uses username and password.
2.  **Local API:** Uses a token and host.

Given that it uses authentication, the `reauthentication-flow` rule applies.

The integration correctly implements the reauthentication flow:

1.  **Triggering Reauthentication:**
    *   In `homeassistant/components/overkiz/__init__.py` (during `async_setup_entry`):
        *   If `client.login()` or subsequent setup calls raise `BadCredentialsException`, `NotSuchTokenException`, or `NotAuthenticatedException`, the integration raises `ConfigEntryAuthFailed` (lines 81-86). This is the standard Home Assistant mechanism to trigger the reauthentication UI flow for the config entry.
    *   In `homeassistant/components/overkiz/coordinator.py` (during `OverkizDataUpdateCoordinator._async_update_data`):
        *   If `client.fetch_events()` or `client.login()` (during re-login attempts) raise `BadCredentialsException` or `NotAuthenticatedException`, the coordinator raises `ConfigEntryAuthFailed` (lines 72-73, 86-88). This ensures that if credentials become invalid after initial setup, the reauth flow is triggered.

2.  **Config Flow Implementation (`homeassistant/components/overkiz/config_flow.py`):**
    *   An `async_step_reauth` method is defined (lines 311-323). This method is called by Home Assistant when reauthentication is needed for an existing config entry.
    *   It correctly retrieves the API type (`_api_type`), server details, and existing credentials (like username for cloud or host for local) from the `entry_data` (which is the current config entry's data).
    *   It then transitions to the `async_step_user` method, passing along the existing entry data. `async_step_user` in turn routes to either `async_step_cloud` or `async_step_local` based on the configuration.
    *   Within `async_step_cloud` (lines 134-192) and `async_step_local` (lines 194-251):
        *   The code checks `if self.source == SOURCE_REAUTH:` to differentiate between a new setup and a reauthentication flow (lines 171, 232).
        *   It presents the appropriate form to the user to re-enter their credentials (e.g., password for cloud, token for local). The username field for cloud API is pre-filled from the existing entry data.
        *   After the user submits new credentials, `async_validate_input` is called to verify them. This function also calls `await self.async_set_unique_id(gateway.id, ...)` to determine the unique ID based on the *new* credentials.
        *   `self._abort_if_unique_id_mismatch(reason="reauth_wrong_account")` is called (lines 172, 233). This crucial step compares the unique ID derived from the newly entered credentials against the unique ID of the config entry being reauthenticated. If they don't match (e.g., user entered credentials for a different gateway), the flow is aborted, preventing accidental misconfiguration.
        *   If validation is successful and unique IDs match, `self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates=user_input)` is called (lines 174-175, 235-236). This correctly updates the existing config entry with the new credentials and reloads the integration. The `_get_reauth_entry()` helper correctly fetches the entry being reauthenticated.

The `overkiz` integration provides a user-friendly way to update credentials for both cloud and local API types, adhering to the requirements of the `reauthentication-flow` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:24:29. Prompt tokens: 87519, Output tokens: 1076, Total tokens: 92245_
