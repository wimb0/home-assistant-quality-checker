# overkiz: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `test-before-configure` rule requires that an integration tests its connection to a device or service within the config flow before a config entry is created. This is to catch issues like incorrect credentials, network problems, or unsupported devices early in the setup process, improving the user experience.

The `overkiz` integration connects to Overkiz-compatible hubs, either via a cloud API or a local API. This involves network communication and authentication, making the `test-before-configure` rule applicable.

The integration **fully follows** this rule. The connection and authentication logic is primarily handled in the `async_validate_input` method within `config_flow.py`. This method is called by both `async_step_cloud` and `async_step_local`, which are the main steps for configuring cloud and local connections, respectively.

In `async_validate_input`:
1.  An `OverkizClient` is initialized with the user-provided data (host, token for local; username, password, hub for cloud).
2.  `await client.login(register_event_listener=False)` is called. This attempts to log in to the Overkiz hub/service. This is the primary connection and authentication test.
3.  `await client.get_gateways()` is called to retrieve gateway information, which also serves as a further test of the connection and token/credentials validity.

Both `async_step_cloud` and `async_step_local` wrap the call to `async_validate_input` in a `try-except-else` block:

`config_flow.py` (simplified structure for `async_step_cloud` and `async_step_local`):
```python
async def async_step_cloud(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
    errors: dict[str, str] = {}
    if user_input:
        # ...
        try:
            # async_validate_input performs the actual connection test (client.login(), etc.)
            await self.async_validate_input(user_input)
        except TooManyRequestsException:
            errors["base"] = "too_many_requests"
        except (BadCredentialsException, NotAuthenticatedException) as exception:
            # ... specific error handling ...
            errors["base"] = "invalid_auth"
        except (TimeoutError, ClientError):
            errors["base"] = "cannot_connect"
        # ... other specific exceptions ...
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Only if async_validate_input succeeds (no exceptions) is the entry created.
            return self.async_create_entry(
                title=user_input[CONF_USERNAME], data=user_input
            )
    # If user_input is None (initial form display) or if errors occurred, show the form again with errors.
    return self.async_show_form(
        step_id="cloud",
        # ...
        errors=errors,
    )
```
This structure ensures:
*   The connection is tested (`client.login()` and `client.get_gateways()` within `async_validate_input`).
*   If `client.login()` or other calls in `async_validate_input` raise an exception (e.g., `BadCredentialsException`, `ClientError`, `TimeoutError`, `TooManyRequestsException`), these are caught by the calling step (`async_step_cloud` or `async_step_local`).
*   Appropriate error messages (`errors["base"] = "some_error_key"`) are set based on the exception.
*   The form is re-shown to the user with these errors (`self.async_show_form(..., errors=errors)`).
*   The config entry is only created (`self.async_create_entry(...)`) in the `else` block, which is executed only if the `try` block (containing `await self.async_validate_input(...)`) completes without raising an exception.

This matches the recommended pattern for the `test-before-configure` rule. Discovery flows (`async_step_dhcp`, `async_step_zeroconf`) and re-authentication (`async_step_reauth`) also correctly channel back into this tested flow.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:14:16. Prompt tokens: 87209, Output tokens: 1113, Total tokens: 90589_
