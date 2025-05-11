# wled: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **todo**                                                                 |

## Overview

The `test-before-configure` rule requires that integrations test the connection to the device or service during the config flow. This is to provide immediate feedback to the user if there are issues like incorrect IP addresses, firewall problems, or unsupported devices, preventing a situation where the integration is set up but doesn't work.

This rule applies to the `wled` integration because WLED devices are network-attached, and the integration needs to establish a connection to a specific WLED device using its hostname or IP address. The integration is not a helper and does not rely on runtime-only auto-discovery in a manner that would exempt it (like Google Cast); it uses Zeroconf for initial discovery to set up a persistent configuration entry for a specific device.

The `wled` integration currently attempts to follow this rule:
1.  In `config_flow.py`, both `async_step_user` and `async_step_zeroconf` call the `_async_get_device(host)` method.
2.  The `_async_get_device` method instantiates a `WLED(host)` client and then calls `await wled.update()`. This `update()` call effectively tests the connection and attempts to retrieve device information.
3.  If `_async_get_device` raises a `WLEDConnectionError` (an exception from the `python-wled` library indicating a direct connection problem), this exception is caught in `async_step_user`, and `errors["base"] = "cannot_connect"` is set. The form is then re-shown with this error. In `async_step_zeroconf`, a `WLEDConnectionError` leads to `self.async_abort(reason="cannot_connect")`.

This correctly handles the most common case of connection failure.

However, the implementation is incomplete when compared to the full error handling strategy recommended by the rule's example. The `python-wled` library's `wled.update()` method can potentially raise other exceptions derived from `WLEDError` (that are not `WLEDConnectionError`) or, in very rare cases, other unexpected Python exceptions if there's an issue within the library call itself not caught by its own top-level handlers.

Currently, the `config_flow.py` only explicitly catches `WLEDConnectionError`:
```python
# In config_flow.py -> WLEDFlowHandler -> async_step_user
# ...
            try:
                device = await self._async_get_device(user_input[CONF_HOST])
            except WLEDConnectionError: # Only catches WLEDConnectionError
                errors["base"] = "cannot_connect"
            else:
                # ... success ...
# ...
```
If `_async_get_device` raises any other type of `WLEDError` or a generic `Exception`, it will not be caught by this block. This would lead to an unhandled exception in the config flow, resulting in a generic error message to the user (e.g., "Config flow failed" or a traceback in logs) rather than a graceful error presented within the form (like "Unknown error occurred"). The rule's example implementation includes a catch-all `except Exception:` to handle such cases and provide a user-friendly `errors["base"] = "unknown"`.

Therefore, while the primary connection test is present, the error handling for all potential failures during this test is not as robust as prescribed, leading to a "todo" status.

## Suggestions

To fully comply with the `test-before-configure` rule and provide a more robust user experience, the config flow should handle other potential exceptions that might occur during the `_async_get_device` call in `async_step_user`.

Modify the `async_step_user` method in `config_flow.py` to include broader exception handling:

```python
# In homeassistant/components/wled/config_flow.py

# Add WLEDError to imports if not already present (it might be implicitly available via wled.WLED)
# from wled import WLED, Device, WLEDConnectionError, WLEDError # Ensure WLEDError is available
# ...
# LOGGER = logging.getLogger(__name__) # Ensure LOGGER is defined if not already

class WLEDFlowHandler(ConfigFlow, domain=DOMAIN):
    # ... (other methods) ...

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            try:
                device = await self._async_get_device(user_input[CONF_HOST])
            except WLEDConnectionError:
                errors["base"] = "cannot_connect"
            except WLEDError:  # Catch other WLED-specific errors
                # These might indicate issues beyond simple connectivity,
                # like unsupported device responses or API issues.
                LOGGER.warning(
                    "WLED configuration failed with an API error for host %s",
                    user_input[CONF_HOST],
                    exc_info=True,
                )
                # Using "cannot_connect" might still be appropriate, or "unknown"
                # if the error is less specific to connectivity.
                errors["base"] = "cannot_connect" # Or "unknown"
            except Exception:  # pylint: disable=broad-except # Catch any other unexpected errors
                LOGGER.exception(
                    "Unexpected exception during WLED setup for host %s",
                    user_input[CONF_HOST],
                )
                errors["base"] = "unknown" # Standard key for generic unknown errors
            else:
                await self.async_set_unique_id(
                    device.info.mac_address, raise_on_progress=False
                )
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: user_input[CONF_HOST]}
                )
                return self.async_create_entry(
                    title=device.info.name,
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors or {},
        )

    # ... (rest of the class) ...
```

**Reasoning for changes:**
*   `except WLEDConnectionError:`: This remains to catch specific connection failures (e.g., host unreachable, timeout).
*   `except WLEDError:`: This new block will catch other errors originating from the `python-wled` library that are not `WLEDConnectionError` (assuming `WLEDConnectionError` is a subclass of `WLEDError`, which is typical). These could be issues like unexpected API responses, authentication problems (if any were relevant here), or device-specific incompatibilities reported by the library. Logging this with `exc_info=True` helps in debugging. Setting `errors["base"]` to `cannot_connect` or `unknown` allows the form to be re-shown with a user-friendly message.
*   `except Exception:`: This is a catch-all for any other unexpected Python exceptions that might occur during the `_async_get_device` call. This ensures the config flow doesn't crash outright and provides a generic "unknown" error to the user, as recommended by the rule's example.

By implementing these additional exception handlers, the `wled` integration will more robustly test the connection and provide appropriate feedback to the user for a wider range of potential issues encountered during the initial setup, fully aligning with the `test-before-configure` rule. A similar robust error handling approach could also be considered for the `_async_get_device` call within `async_step_zeroconf` to ensure it also aborts gracefully with an appropriate reason for all failure types.

_Created at 2025-05-10 19:29:55. Prompt tokens: 22146, Output tokens: 1878, Total tokens: 29571_
