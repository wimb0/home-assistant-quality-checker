# paperless_ngx: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [paperless_ngx](https://www.home-assistant.io/integrations/paperless_ngx/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `reconfiguration-flow` rule requires integrations to provide a way for users to update their configuration (e.g., host, API key) without needing to delete and re-add the integration. This is particularly useful if server details change or credentials need to be updated.

This rule applies to the `paperless_ngx` integration because it is configured using a URL and an API key, as defined in its `config_flow.py` (`STEP_USER_DATA_SCHEMA`). These are settings that a user might need to change post-setup (e.g., if the Paperless-ngx server URL changes or the API key is regenerated).

Currently, the `paperless_ngx` integration does **not** follow this rule. Its `config_flow.py` (specifically the `PaperlessConfigFlow` class) only implements the `async_step_user` method for initial setup. It lacks the `async_step_reconfigure` method, which is necessary to allow users to modify an existing configuration entry.

## Suggestions

To make the `paperless_ngx` integration compliant with the `reconfiguration-flow` rule, an `async_step_reconfigure` method should be added to the `PaperlessConfigFlow` class in `homeassistant/components/paperless_ngx/config_flow.py`.

This method would:
1.  Be triggered when a user initiates a "Reconfigure" action for an existing `paperless_ngx` config entry.
2.  Display a form, pre-filled with the current `CONF_URL` and `CONF_API_KEY` from the existing config entry.
3.  Allow the user to submit new values for these fields.
4.  Validate the new credentials by attempting to connect to the Paperless-ngx instance, similar to the validation logic in `async_step_user`.
5.  If validation is successful, update the existing config entry with the new data and reload the integration.
6.  If validation fails, show appropriate errors on the form.

Here's an example of how the `async_step_reconfigure` method could be implemented:

```python
# In homeassistant/components/paperless_ngx/config_flow.py

from pypaperless import Paperless
from pypaperless.exceptions import (
    InitializationError,
    PaperlessConnectionError,
    PaperlessForbiddenError,
    PaperlessInactiveOrDeletedError,
    PaperlessInvalidTokenError,
)
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class PaperlessConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Paperless-ngx."""

    VERSION = 1 # Add version if not already present

    # async_step_user method remains as is...
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # ... (current implementation)
        if user_input is not None:
            self._async_abort_entries_match(
                {
                    CONF_URL: user_input[CONF_URL],
                    CONF_API_KEY: user_input[CONF_API_KEY],
                }
            )

        errors: dict[str, str] = {}
        if user_input is not None:
            client = Paperless(
                user_input[CONF_URL],
                user_input[CONF_API_KEY],
                session=async_get_clientsession(self.hass),
            )

            try:
                await client.initialize()
                await client.statistics() # Test API access
            except PaperlessConnectionError:
                errors[CONF_URL] = "cannot_connect"
            except PaperlessInvalidTokenError:
                errors[CONF_API_KEY] = "invalid_api_key"
            except PaperlessInactiveOrDeletedError:
                errors[CONF_API_KEY] = "user_inactive_or_deleted"
            except PaperlessForbiddenError:
                errors[CONF_API_KEY] = "forbidden"
            except InitializationError:
                errors[CONF_URL] = "cannot_connect"
            except Exception as err:  # noqa: BLE001
                LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_URL], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        # self.config_entry is available here because this flow is initiated for an existing entry
        entry = self.config_entry
        if not entry:
            # Should not happen
            return self.async_abort(reason="unknown_error")

        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the new user_input
            client = Paperless(
                user_input[CONF_URL],
                user_input[CONF_API_KEY],
                session=async_get_clientsession(self.hass),
            )
            try:
                await client.initialize()
                await client.statistics() # Test API access with new credentials
            except PaperlessConnectionError:
                errors[CONF_URL] = "cannot_connect"
            except PaperlessInvalidTokenError:
                errors[CONF_API_KEY] = "invalid_api_key"
            except PaperlessInactiveOrDeletedError:
                errors[CONF_API_KEY] = "user_inactive_or_deleted"
            except PaperlessForbiddenError:
                errors[CONF_API_KEY] = "forbidden"
            except InitializationError:
                errors[CONF_URL] = "cannot_connect" # Could be a different error key if desired
            except Exception as err:  # noqa: BLE001
                LOGGER.exception("Unexpected exception during reconfigure: %s", err)
                errors["base"] = "unknown"
            else:
                # Update the config entry with new data and new title
                # self.async_update_reload_and_abort is preferred as it also reloads the entry
                return self.async_update_reload_and_abort(
                    entry,
                    data=user_input,
                    title=user_input[CONF_URL], # Update title if it's derived from data
                )

        # Show the form, pre-filled with current values from the config entry
        # Make sure the schema is consistent with STEP_USER_DATA_SCHEMA
        # but provide defaults from the existing entry.
        reconfigure_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=entry.data.get(CONF_URL)): str,
                vol.Required(CONF_API_KEY, default=entry.data.get(CONF_API_KEY)): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=reconfigure_schema,
            errors=errors,
            description_placeholders=None, # Add if helpful
        )

    # If the integration supports options flows, a reconfigure listener might also be needed
    # or handled differently. For simple data changes like this, the above is standard.
    # However, the rule implies that a reconfigure flow is an alternative to an options flow
    # for core settings like host/API key.
    # The example in the rule description does not show adding an options listener.
```

**Why these changes satisfy the rule:**
*   Adding `async_step_reconfigure` makes the integration discoverable by Home Assistant's UI for reconfiguration.
*   The flow allows users to modify the essential connection parameters (`CONF_URL`, `CONF_API_KEY`).
*   Using `self.async_update_reload_and_abort` ensures that the configuration is updated, and the integration is reloaded with the new settings, providing a seamless update experience without requiring manual deletion and re-addition.

This change would improve user experience by allowing easier updates to the Paperless-ngx server connection details if they change.

_Created at 2025-05-27 13:08:59. Prompt tokens: 5934, Output tokens: 2130, Total tokens: 12738_
