# evohome: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `test-before-configure` rule requires integrations to test the connection to a device or service during the config flow, before the configuration entry is created. This helps catch issues like incorrect credentials, network problems, or unsupported devices early, improving the user experience.

This rule applies to the `evohome` integration because it connects to the Honeywell Total Connect Comfort cloud service, which requires authentication and network connectivity. The integration uses a config flow (`config_flow: true` in `manifest.json`) to set up user credentials.

The `evohome` integration **follows** this rule.

In `homeassistant/components/evohome/config_flow.py`, the `async_step_user` method is responsible for handling user input (username and password).
1.  It calls `self._test_credentials(username, password)`.
    *   Inside `_test_credentials`, a `TokenManager` is instantiated.
    *   Crucially, `await token_manager.get_access_token()` is called. The `_load_token_data` method used by the `TokenManager` during the config flow is designed to `return None`, forcing `get_access_token` to attempt a fresh token retrieval from the vendor's API. This effectively tests the provided credentials and basic connectivity to the authentication service.
    *   `_test_credentials` catches specific exceptions like `ec2.BadUserCredentialsError` (raising `ConfigEntryAuthFailed("invalid_auth")`) and `ec2.AuthenticationFailedError` (raising `ConfigEntryNotReady("rate_exceeded")` or `ConfigEntryNotReady("cannot_connect")`).
2.  If `_test_credentials` is successful, it returns a client instance. Then, `async_step_user` calls `self._test_installation(client)`.
    *   Inside `_test_installation`, `await client.update(dont_update_status=True)` is called. This attempts to fetch the user's installation data (locations) from the Evohome API, further verifying that the authenticated account is valid and can access data.
    *   This method also catches `ec2.ApiRequestFailedError` and raises appropriate `ConfigEntryNotReady` exceptions (e.g., "rate_exceeded", "cannot_connect").
3.  Back in `async_step_user`, these exceptions (`ConfigEntryAuthFailed`, `ConfigEntryNotReady`) are caught, and an error message is prepared for the user by setting `errors["base"]`.
    ```python
    # homeassistant/components/evohome/config_flow.py
    # Snippet from async_step_user
    try:
        self._client = await self._test_credentials(
            self._username,
            user_input[CONF_PASSWORD],
        )
        self._num_locations = await self._test_installation(self._client)
    except AbortFlow as err:
        errors["base"] = str(err.reason)
    except (ConfigEntryAuthFailed, ConfigEntryNotReady) as err:
        if str(err) not in ("rate_exceeded", "cannot_connect", "invalid_auth"):
            raise  # pragma: no cover
        errors["base"] = str(err)
    else:
        self._password = user_input[CONF_PASSWORD]
        return await self.async_step_location() # Proceeds only on success

    # ...
    return self.async_show_form(
        step_id="user", data_schema=data_schema, errors=errors # Re-shows form with errors
    )
    ```
4.  If any errors occur during these test calls, the `async_show_form` method is called with the `errors` dictionary, displaying the relevant error message to the user. The config flow does not proceed to create an entry.
5.  Only if both `_test_credentials` and `_test_installation` succeed without raising an exception does the flow proceed (e.g., to `async_step_location` and then to `_update_or_create_entry` for entry creation).

This mechanism ensures that credentials, connectivity, and basic API functionality are verified before the configuration entry is created, fully aligning with the `test-before-configure` rule. The reauthentication flow (`async_step_reauth_confirm`) also utilizes `_test_credentials` in a similar manner.

## Suggestions

No suggestions needed.

---

_Created at 2025-05-29 11:47:40. Prompt tokens: 22039, Output tokens: 1117, Total tokens: 26099._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
