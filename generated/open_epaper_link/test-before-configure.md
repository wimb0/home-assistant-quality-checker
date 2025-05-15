# open_epaper_link: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `test-before-configure` rule requires that integrations test the connection to a device or service during the config flow, before the configuration entry is created. This helps catch issues like incorrect IP addresses, firewall problems, or wrong credentials early, improving the user experience.

This rule applies to the `open_epaper_link` integration because:
1.  It connects to a network device (the OpenEPaperLink Access Point).
2.  The initial setup is performed via a config flow where the user provides the host of the Access Point, not solely through runtime auto-discovery for the AP itself.

The `open_epaper_link` integration **fully follows** this rule.

The connection test is implemented in the `config_flow.py` file, specifically within the `ConfigFlow` class and its `_validate_input` method.

When a user submits the host in the `async_step_user` method:
1.  The `_validate_input(self, host: str)` method is called:
    ```python
    # homeassistant/components/open_epaper_link/config_flow.py
    async def _validate_input(self, host: str) -> tuple[dict[str, str], str | None]:
        errors = {}
        # ... host sanitization ...
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(f"http://{host}") as response: # Test call
                    if response.status != 200:
                        errors["base"] = "cannot_connect"
                    else:
                        self._host = host
                        return {"title": f"OpenEPaperLink AP ({host})"}, None # Success
        except asyncio.TimeoutError:
            errors["base"] = "timeout"
        except aiohttp.ClientError:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        return {}, errors.get("base", "unknown") # Failure with error code
    ```
2.  This method attempts an HTTP GET request to the root of the provided host.
3.  It checks if the response status is 200. If not, it sets `errors["base"] = "cannot_connect"`.
4.  It handles specific exceptions like `asyncio.TimeoutError` (setting `errors["base"] = "timeout"`) and `aiohttp.ClientError` (setting `errors["base"] = "cannot_connect"`). A generic `Exception` catch-all sets `errors["base"] = "unknown"`.
5.  Back in `async_step_user`:
    ```python
    # homeassistant/components/open_epaper_link/config_flow.py
    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ):
        errors: dict[str, str] = {}
        if user_input is not None:
            info, error = await self._validate_input(user_input[CONF_HOST])
            if not error: # Only create entry if validation passed
                await self.async_set_unique_id(self._host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info["title"],
                    data={CONF_HOST: self._host}
                )
            errors["base"] = error # Pass error to form
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors, # Show errors to the user
        )
    ```
    If `_validate_input` returns an error, `self.async_create_entry` is not called. Instead, `self.async_show_form` is called again, displaying the relevant error message to the user. The entry is only created if `_validate_input` succeeds (i.e., `error` is `None`).

This implementation directly matches the requirements and example provided by the `test-before-configure` rule. The reauthentication flow (`async_step_reauth_confirm`) also correctly utilizes `_validate_input` to re-test the connection.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 20:39:49. Prompt tokens: 60698, Output tokens: 1125, Total tokens: 63929_
