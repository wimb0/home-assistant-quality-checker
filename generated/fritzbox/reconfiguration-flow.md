```markdown
# fritzbox: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow) |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `reconfiguration-flow` rule requires integrations with configurable settings to provide a configuration flow step (`async_step_reconfigure`) allowing users to update those settings (like host, username, password) without removing and re-adding the integration.

This rule applies to the `fritzbox` integration because its configuration flow (`homeassistant/components/fritzbox/config_flow.py`) requires the user to input configurable details such as `CONF_HOST`, `CONF_USERNAME`, and `CONF_PASSWORD` (see `DATA_SCHEMA_USER`).

The integration **partially** follows this rule. It does have an `async_step_reconfigure` method in `config_flow.py`. This method is designed to allow users to update the configuration. However, the form presented in this step (defined within `async_step_reconfigure`) currently **only allows changing the `CONF_HOST`**. It does not provide fields for updating the `CONF_USERNAME` or `CONF_PASSWORD`.

The rule's description and example implementation suggest that the reconfigure flow should cover the key configuration parameters that might change. While the `fritzbox` integration correctly implements a separate `reauthentication-flow` (`async_step_reauth`) to handle authentication failures (which might involve changing the password), the `reconfigure` flow is intended for intentional configuration updates regardless of connection status. By only allowing the host to be changed, it limits the user's ability to correct or update other parts of the configuration via the reconfigure flow itself.

Therefore, the integration does not fully implement the required reconfiguration capabilities for all configurable settings.

## Suggestions

To fully comply with the `reconfiguration-flow` rule, the `async_step_reconfigure` method should be updated to allow changing all relevant configurable fields. In the case of the `fritzbox` integration, this means including `CONF_USERNAME` and `CONF_PASSWORD` in the form presented during the reconfigure step, in addition to the already present `CONF_HOST`.

Here are the specific steps:

1.  **Modify the schema in `async_step_reconfigure`:** Update the `vol.Schema` within the `async_show_form` call to include `CONF_USERNAME` and `CONF_PASSWORD`. You can pre-fill the default values for these fields from the existing config entry data, similar to how the host is currently pre-filled.
2.  **Update data retrieval in the `user_input` block:** When `user_input` is received, retrieve the values for `CONF_HOST`, `CONF_USERNAME`, and `CONF_PASSWORD` from `user_input`.
3.  **Use the new credentials for connection test:** The existing `async_try_connect()` call already uses the credentials stored in `self._host`, `self._username`, and `self._password`. Ensure these are set from the `user_input` before calling `async_try_connect`.
4.  **Update the config entry with all new data:** In the `RESULT_SUCCESS` block, update the config entry using `self.async_update_reload_and_abort`. The `data_updates` dictionary should include all fields that were presented in the form: `CONF_HOST`, `CONF_USERNAME`, and `CONF_PASSWORD`.

Example modification for `async_step_reconfigure`:

```python
    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        errors = {}
        reconfigure_entry = self._get_reconfigure_entry() # Get the current entry

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._username = user_input[CONF_USERNAME] # Get username from input
            self._password = user_input[CONF_PASSWORD] # Get password from input

            result = await self.async_try_connect()

            if result == RESULT_SUCCESS:
                # Update ALL fields from user_input
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={
                        CONF_HOST: self._host,
                        CONF_USERNAME: self._username,
                        CONF_PASSWORD: self._password,
                    },
                )
            errors["base"] = result

        # Schema for the form - include username and password, pre-filled
        host = reconfigure_entry.data[CONF_HOST]
        username = reconfigure_entry.data[CONF_USERNAME]

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=host): str,
                    vol.Required(CONF_USERNAME, default=username): str,
                    vol.Required(CONF_PASSWORD): str, # Password should not be pre-filled for security
                }
            ),
            description_placeholders={"name": host},
            errors=errors,
        )
```

Implementing these changes will ensure that the `reconfigure` flow allows users to update any of the core configuration settings required by the integration without forcing them to remove and re-add it, thus fully satisfying the rule's requirements. The existing `reauth` flow should remain specifically for handling authentication failure events.

```


_Created at 2025-05-25 11:37:38. Prompt tokens: 19466, Output tokens: 1305, Total tokens: 21964_
