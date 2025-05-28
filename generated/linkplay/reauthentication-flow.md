# linkplay: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **exempt**                                       |
| Reason | The integration connects to devices via local IP address and does not use user-specific credentials (like passwords or API tokens) that would require a reauthentication flow if changed. |

## Overview

The `reauthentication-flow` rule requires integrations that use authentication (e.g., username/password, API tokens) to provide a UI flow for users to update these credentials if they change, without needing to delete and re-add the integration.

The `linkplay` integration facilitates communication with LinkPlay-enabled devices on the local network. Configuration involves discovering these devices via Zeroconf or manually providing their host IP address.

Upon reviewing the `linkplay` integration's code, specifically `config_flow.py`:
*   The `async_step_user` method collects only the `CONF_HOST` (IP address or hostname) of the LinkPlay device:
    ```python
    # config_flow.py
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # ...
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )
    ```
*   The data stored in the config entry is also limited to the host:
    ```python
    # config_flow.py
    return self.async_create_entry(
        title=self.data[CONF_MODEL],
        data={CONF_HOST: self.data[CONF_HOST]},
    )
    ```
*   There are no prompts for, or storage of, usernames, passwords, API keys, or other similar credentials that might expire or be changed by the user.
*   The communication with the device, handled by the `python-linkplay` library, appears to be direct IP-based communication to the device's local API, which typically does not involve user-settable passwords for API access.

The rule's exception states: "If the integration doesn't require any form of authentication, this rule doesn't apply." Since `linkplay` authenticates or, more accurately, connects to devices based on their network address rather than user-specific, changeable credentials, this rule is not applicable. Issues like a changed IP address would be a connection failure or potentially handled by discovery updates or a reconfiguration flow, not a reauthentication flow for credentials.

The `config_flow.py` does not contain `async_step_reauth` or `async_step_reauth_confirm` methods, which would be indicative of implementing this rule. This absence is appropriate given the integration's connection mechanism.

Therefore, the `linkplay` integration is exempt from the `reauthentication-flow` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 15:02:31. Prompt tokens: 12816, Output tokens: 726, Total tokens: 15111_
