```markdown
# fritzbox: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that integrations needing authentication provide a reauthentication flow via the UI, allowing users to update credentials without removing and re-adding the integration. This rule is applicable to the `fritzbox` integration as it requires username and password for connecting to the FRITZ!Box router.

The `fritzbox` integration fully follows this rule.

1.  **Triggering Reauthentication:** The `FritzboxDataUpdateCoordinator` in `homeassistant/components/fritzbox/coordinator.py` catches `LoginError` from the `pyfritzhome` library during the `_update_fritz_devices` method. When a `LoginError` occurs, it raises `ConfigEntryAuthFailed`, which signals to Home Assistant's config entry system that reauthentication is required.

    ```python
    # homeassistant/components/fritzbox/coordinator.py
    ...
    except HTTPError:
        # If the device rebooted, login again
        try:
            self.fritz.login()
        except LoginError as ex:
            raise ConfigEntryAuthFailed from ex # <--- Triggers reauth
        self.fritz.update_devices(ignore_removed=False)
    ...
    ```

2.  **Handling the Reauthentication Flow:** The `FritzboxConfigFlow` in `homeassistant/components/fritzbox/config_flow.py` implements the `async_step_reauth` and `async_step_reauth_confirm` methods.
    *   `async_step_reauth` is triggered by Home Assistant when `ConfigEntryAuthFailed` is raised. It initializes the flow with the existing host and username from the configuration entry and then proceeds to the `reauth_confirm` step.
    *   `async_step_reauth_confirm` displays a form asking the user for the username and password. Upon submission (`user_input`), it calls `async_try_connect` with the provided credentials. If successful (`RESULT_SUCCESS`), it updates the existing configuration entry data using `self.async_update_reload_and_abort` and the new credentials, satisfying the rule's requirement to update the entry. If authentication fails again (`RESULT_INVALID_AUTH`), it shows an error on the form.

    ```python
    # homeassistant/components/fritzbox/config_flow.py
    ...
    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Trigger a reauthentication flow."""
        self._host = entry_data[CONF_HOST]
        self._name = str(entry_data[CONF_HOST])
        self._username = entry_data[CONF_USERNAME]

        return await self.async_step_reauth_confirm() # <--- Proceeds to confirm step

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthorization flow."""
        errors = {}

        if user_input is not None:
            self._password = user_input[CONF_PASSWORD]
            self._username = user_input[CONF_USERNAME] # <--- Gets new credentials

            result = await self.async_try_connect() # <--- Tries to connect

            if result == RESULT_SUCCESS:
                return self.async_update_reload_and_abort( # <--- Updates entry on success
                    self._get_reauth_entry(),
                    data={
                        CONF_HOST: self._host,
                        CONF_PASSWORD: self._password,
                        CONF_USERNAME: self._username,
                    },
                )
            if result != RESULT_INVALID_AUTH:
                return self.async_abort(reason=result)
            errors["base"] = result

        return self.async_show_form( # <--- Shows the reauth form
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=self._username): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            description_placeholders={"name": self._name},
            errors=errors,
        )
    ...
    ```

The implementation correctly handles the authentication failure during updates and provides a UI flow to update credentials and persist them in the configuration entry.

## Suggestions

No suggestions needed. The integration correctly implements the reauthentication flow as required by the rule.
```

_Created at 2025-05-25 11:35:13. Prompt tokens: 19510, Output tokens: 1128, Total tokens: 21294_
