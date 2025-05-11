# home_connect: config-flow-test-coverage

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [config-flow-test-coverage](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow-test-coverage)                                                     |
| Status | **todo**                                                                 |

## Overview

The `config-flow-test-coverage` rule requires 100% test coverage for the config flow, including any reauthentication, reconfiguration, and options flows. These tests must verify that the flow can recover from errors and ensure the uniqueness of config entries.

The `home_connect` integration uses an OAuth2-based config flow, defined in `config_flow.py`. This flow handles initial user setup and reauthentication. The `manifest.json` confirms `config_flow: true` and indicates support for discovery via `zeroconf` and `dhcp`.

However, the crucial file `tests/test_config_flow.py` (or an equivalent file containing config flow tests) was **not provided** in the input. The absence of this file implies that there are no tests for the config flow, reauthentication flow, or discovery-initiated flows.

Therefore, the integration currently does not meet the `config-flow-test-coverage` rule because:
1.  There is no evidence of any test file for `config_flow.py`.
2.  Consequently, there are no tests for the user setup flow, reauthentication flow, error handling within these flows, or uniqueness checks for configuration entries.
3.  While discovery is supported, tests for discovery-initiated flows are also presumed missing.
4.  The integration does not appear to implement a separate options flow or a reconfigure flow, so tests for these are not applicable at this time. If they were to be added, they would also require full test coverage.

## Suggestions

To comply with the `config-flow-test-coverage` rule, a test file, typically `tests/test_config_flow.py`, needs to be created and populated with comprehensive tests.

**1. Create `tests/test_config_flow.py`:**
   If it doesn't exist, create this file.

**2. Test User-Initiated Setup Flow:**
   The primary flow is the OAuth2 setup.
   *   **Happy Path:**
      ```python
      # tests/test_config_flow.py
      from unittest.mock import patch
      import jwt # If needed for mocking token details

      from homeassistant import config_entries, data_entry_flow
      from homeassistant.core import HomeAssistant
      from homeassistant.helpers import config_entry_oauth2_flow

      from pytest_homeassistant_custom_component.common import MockConfigEntry

      from custom_components.home_connect.const import DOMAIN # Adjust import if necessary

      async def test_full_user_flow_success(hass: HomeAssistant, hass_client_no_auth) -> None:
          """Test the full user setup flow successfully creates an entry."""
          # Setup mocks for OAuth2 session and token data
          # result = await hass.config_entries.flow.async_init(
          #     DOMAIN, context={"source": config_entries.SOURCE_USER}
          # )
          # # Simulate user interaction if AbstractOAuth2FlowHandler presents a form
          # # ...
          # # Simulate OAuth callback with valid token data
          # with patch(
          #     "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
          #     # ... mock implementation ...
          # ), patch(
          #     "custom_components.home_connect.config_flow.jwt.decode" # or where jwt.decode is used
          # ) as mock_jwt_decode:
          #     mock_jwt_decode.return_value = {"sub": "test_user_id"}
          #     # Assume AbstractOAuth2FlowHandler handles the external part
          #     # We need to trigger the async_oauth_create_entry
          #     # This might involve mocking AbstractOAuth2Implementation.async_resolve_external_data
          #     # and then calling async_configure on the flow with the result.

          # # A more direct way to test async_oauth_create_entry if OAuth steps are complex to mock:
          # flow_handler = config_entry_oauth2_flow.OAuth2FlowHandler() # Use your actual handler
          # flow_handler.hass = hass
          # flow_handler.handler = DOMAIN
          # flow_handler.flow_id = "some_flow_id" # May need to initialize properly

          # mock_data = {
          #     "auth_implementation": DOMAIN, # Or actual implementation key
          #     "token": {"access_token": "mock_access_token", "expires_in": 3600}
          # }
          # with patch("custom_components.home_connect.config_flow.jwt.decode") as mock_jwt_decode, \
          #      patch("homeassistant.helpers.config_entry_oauth2_flow.AbstractOAuth2FlowHandler._async_retrieve_token", return_value=mock_data["token"]):
          #     mock_jwt_decode.return_value = {"sub": "test_user_id"}
          #
          #     result = await hass.config_entries.flow.async_init(
          #         DOMAIN, context={"source": config_entries.SOURCE_USER}
          #     )
          #     # This typically shows a link to the auth provider
          #     assert result["type"] == data_entry_flow.FlowResultType.EXTERNAL_STEP 
          #
          #     # Simulate the callback from the auth provider
          #     result2 = await hass.config_entries.flow.async_configure(
          #         result["flow_id"], user_input={"code": "mock_code", "state": result["external_step_url"].split("state=")[1].split("&")[0]}
          #     )
          #     # This might involve further mocking depending on AbstractOAuth2Implementation

          # Assert entry is created
          # assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
          # assert result2["title"] == "Home Connect" # Or based on user/account
          # assert result2["data"] == mock_data
          # assert result2["result"].unique_id == "test_user_id"
      ```
      *Self-correction: Testing OAuth flows can be tricky. The example above is a sketch. Refer to core tests for `AbstractOAuth2FlowHandler` for better patterns. Key is to mock `async_resolve_external_data` or the token retrieval part.*
      A more common pattern for testing OAuth flows involves mocking the `AbstractOAuth2Implementation`.
      Example structure:
      ```python
      async def test_user_flow(hass: HomeAssistant, current_request_with_host: None) -> None:
          """Test user initiated flow."""
          result = await hass.config_entries.flow.async_init(
              DOMAIN, context={"source": config_entries.SOURCE_USER}
          )
          state = config_entry_oauth2_flow._encode_jwt(hass, {"flow_id": result["flow_id"]}) # Simplified

          assert result["type"] == data_entry_flow.FlowResultType.EXTERNAL_STEP
          assert result["url"].startswith("https://api.home-connect.com/security/oauth/authorize?") # From aiohomeconnect

          # Simulate callback
          with patch("custom_components.home_connect.config_flow.jwt.decode", return_value={"sub": "test_user_sub"}), \
               patch("homeassistant.components.home_connect.api.AsyncConfigEntryAuth.async_get_access_token", return_value="mock-token"), \
               patch("homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_ensure_token_valid", return_value=None), \
               patch("homeassistant.helpers.config_entry_oauth2_flow.AbstractOAuth2Implementation.async_resolve_external_data", return_value={"token": {"access_token": "mock_access_token", "id_token": "mock_id_token", "expires_in": 3600}}), \
               patch("custom_components.home_connect.async_setup_entry", return_value=True) as mock_setup_entry: # Mock setup to prevent full integration load

              result2 = await hass.config_entries.flow.async_configure(
                  result["flow_id"], {"code": "mock_code", "state": state}
              )

          assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
          assert result2["title"] # Check title based on what it should be
          assert result2["data"]["auth_implementation"] == DOMAIN
          assert result2["data"]["token"]["access_token"] == "mock_access_token"
          assert len(mock_setup_entry.mock_calls) == 1
          # Check unique_id of the created entry
          entry = hass.config_entries.async_entries(DOMAIN)[0]
          assert entry.unique_id == "test_user_sub"
      ```

   *   **Error Handling:**
        *   Mock OAuth failures (e.g., `async_resolve_external_data` raising an error or returning invalid data) and verify the flow shows an error or aborts correctly (e.g., `oauth_error`, `oauth_failed`).
        *   Test scenario where `jwt.decode` fails if the token is malformed (though `AbstractOAuth2FlowHandler` might catch this earlier).

   *   **Uniqueness Check:**
        *   Successfully set up one entry.
        *   Attempt to set up another entry that would result in the same unique ID (mock `jwt.decode` to return the same `sub`).
        *   Verify the flow aborts with `reason="already_configured"`.
        ```python
        # Example for uniqueness test
        # ... (setup first entry) ...
        # result = await hass.config_entries.flow.async_init(
        #     DOMAIN, context={"source": config_entries.SOURCE_USER}
        # )
        # # ... (simulate OAuth again, ensuring jwt.decode returns the same "sub")
        # with patch("custom_components.home_connect.config_flow.jwt.decode", return_value={"sub": "test_user_sub"}):
        #    # ... (simulate external callback for the second flow)
        #    result2 = await hass.config_entries.flow.async_configure(...) 
        # assert result2["type"] == data_entry_flow.FlowResultType.ABORT
        # assert result2["reason"] == "already_configured"
        ```

**3. Test Reauthentication Flow:**
   *   Set up an initial `MockConfigEntry`.
   *   Initiate the reauth flow: `await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id}, data=entry.data)`.
   *   **Happy Path:**
        *   Verify `async_step_reauth_confirm` is shown.
        *   Simulate user confirmation.
        *   Mock successful OAuth token refresh.
        *   Mock `jwt.decode` to return the *same* unique ID (`sub`).
        *   Verify the entry is updated/reloaded (`async_update_reload_and_abort`).
   *   **Error Handling:**
        *   Mock OAuth failure during reauth and check for appropriate error/abort.
        *   Test reauth with a *different* account: Mock `jwt.decode` to return a *different* unique ID (`sub`) than the original entry. Verify the flow aborts with `reason="wrong_account"`.

**4. Test Discovery-Initiated Flow (if applicable):**
   *   If discovery (`zeroconf` or `dhcp`) can initiate the flow and has any specific steps or pre-filling before handing off to the OAuth process, test these.
   *   Often, discovery simply provides data that then leads to the standard user OAuth flow. If so, ensure tests cover `hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=discovery_data)`.
   *   The current `config_flow.py` for `home_connect` does not define explicit `async_step_zeroconf` or `async_step_dhcp` methods, meaning discovery likely falls back to `async_step_user` which initiates the OAuth flow. Test that this initiation path works and leads to the OAuth external step.

**5. General Test Practices:**
   *   Use `pytest-homeassistant-custom-component.common.MockConfigEntry`.
   *   Use `unittest.mock.patch` extensively to control dependencies and simulate API responses/failures.
   *   Assert flow results (`type`, `step_id`, `errors`, `reason` for aborts).
   *   Verify data in `CREATE_ENTRY` results.
   *   Ensure error messages or forms are shown to the user, allowing them to recover or retry where appropriate. For OAuth, this is often handled by `AbstractOAuth2FlowHandler`, but tests should confirm this behavior.

By implementing these tests, the `home_connect` integration can achieve the required 100% test coverage for its config and reauth flows, ensuring a more robust user experience.

_Created at 2025-05-10 20:20:10. Prompt tokens: 139991, Output tokens: 3125, Total tokens: 147019_
