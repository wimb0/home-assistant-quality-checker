# open_epaper_link: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **exempt**                                       |
| Reason | The integration connects to the OpenEPaperLink AP via its host/IP address and does not use any authentication credentials (like API keys, usernames, or passwords) that would require a reauthentication flow if changed. The rule's exception for integrations not requiring authentication applies. |

## Overview

The `reauthentication-flow` rule requires integrations that use authentication to provide a UI flow for users to update their credentials (e.g., API tokens, passwords) if they change or expire, without needing to delete and re-add the integration. The rule includes an exception: "If the integration doesn't require any form of authentication, this rule doesn't apply."

The `open_epaper_link` integration connects to an OpenEPaperLink Access Point (AP) using a host address (IP or hostname). The setup process, as defined in `config_flow.py`, only asks for the `CONF_HOST`:
```python
# homeassistant/components/open_epaper_link/config_flow.py
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)
```
The `_validate_input` method verifies the connection by making a simple HTTP GET request to the provided host, without any API tokens, passwords, or other forms of credentials:
```python
# homeassistant/components/open_epaper_link/config_flow.py
async def _validate_input(self, host: str) -> tuple[dict[str, str], str | None]:
    # ...
    try:
        session = async_get_clientsession(self.hass)
        async with asyncio.timeout(10):
            async with session.get(f"http://{host}") as response: # No authentication headers/tokens
                if response.status != 200:
                    errors["base"] = "cannot_connect"
                else:
                    self._host = host
                    return {"title": f"OpenEPaperLink AP ({host})"}, None
    # ...
```
Subsequent communication with the AP, such as in `services.py` (e.g., `upload_image`) or `util.py` (e.g., `send_tag_cmd`), also relies on direct HTTP requests to the host without authentication tokens or credentials.

The `config_flow.py` file *does* implement `async_step_reauth` and `async_step_reauth_confirm`. However, this flow is designed to re-validate the existing host, not to collect new credentials. The `async_step_reauth_confirm` method, when showing a form upon failure or for confirmation, does not include a `data_schema` to prompt the user for new credentials, which is a key part of the rule's example implementation:
```python
# homeassistant/components/open_epaper_link/config_flow.py
    async def async_step_reauth_confirm(
            self, user_input: dict[str, Any] | None = None
    ):
        # ...
        if user_input is not None: # This block is not reachable if no form with input is presented
            # ... (This part is for handling form submission, which isn't presented for credential input)
            pass

        # If initial call (user_input is None) or if validation fails:
        # ...
        # info, error = await self._validate_input(self._host) # Tries to validate existing host
        # ...
        return self.async_show_form(
            step_id="reauth_confirm",
            description_placeholders={"host": self._host}, # No data_schema for new credentials
            errors=errors,
        )
```
This differs significantly from the rule's example, which shows a `data_schema` for inputting a new `CONF_API_TOKEN`. The `open_epaper_link` reauth flow does not allow the user to "provide the new credentials to use from now on," as the rule specifies.

Since the integration does not use authentication credentials (like API keys or passwords) that might be changed by the user on the service side, the primary mechanism for reauthentication as described by the rule is not applicable. The host address is a connection parameter, not a credential in this context. Therefore, the integration falls under the rule's exception.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 20:53:21. Prompt tokens: 61008, Output tokens: 1094, Total tokens: 65459_
