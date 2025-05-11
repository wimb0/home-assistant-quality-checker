# wled: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not manage authentication credentials (e.g., password, API token) that would necessitate a reauthentication flow. |

## Overview

The `reauthentication-flow` rule mandates that integrations using authentication (like API tokens or passwords) must provide a UI flow for users to update these credentials if they become invalid, without needing to delete and re-add the integration.

The `wled` integration connects to WLED devices based on their IP address or hostname. Analyzing the integration's `config_flow.py`:
*   The `async_step_user` method only prompts for the `CONF_HOST` (hostname or IP address).
    ```python
    # config_flow.py
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # ...
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors or {},
        )
    ```
*   There are no prompts or storage mechanisms for passwords, API tokens, or other authentication credentials.
*   The underlying `python-wled` library, as used in `coordinator.py`, is initialized with just the host:
    ```python
    # coordinator.py
    self.wled = WLED(entry.data[CONF_HOST], session=async_get_clientsession(hass))
    ```
    The `WLED` class from the library does not take authentication parameters like tokens or passwords. WLED devices can have a password for their web UI, but the JSON API used by this integration is typically accessible without authentication.

Since the `wled` integration does not handle any authentication credentials that could become invalid (e.g., a changed password or an expired API token), the requirement for a reauthentication flow to update such credentials does not apply. The rule includes an exception: "If the integration doesn't require any form of authentication, this rule doesn't apply."

Therefore, the `wled` integration is **exempt** from the `reauthentication-flow` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:57:02. Prompt tokens: 23431, Output tokens: 591, Total tokens: 26135_
