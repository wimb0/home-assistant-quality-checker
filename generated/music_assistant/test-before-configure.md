# music_assistant: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `test-before-configure` rule requires that integrations test the connection to a device or service during the config flow to provide immediate feedback to the user about potential issues like incorrect credentials, network problems, or unsupported devices.

This rule applies to the `music_assistant` integration because it connects to an external Music Assistant server via a URL, which can be subject to various connectivity issues. The integration uses a config flow (`"config_flow": true` in `manifest.json`) for setup.

The `music_assistant` integration correctly follows this rule:

1.  **User-initiated configuration (`async_step_user`):**
    In `config_flow.py`, the `async_step_user` method handles manual configuration. When user input is provided (containing the server URL):
    *   It calls the `get_server_info` helper function:
        ```python
        # homeassistant/components/music_assistant/config_flow.py
        async def async_step_user(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            errors: dict[str, str] = {}
            if user_input is not None:
                try:
                    self.server_info = await get_server_info(
                        self.hass, user_input[CONF_URL]
                    )
                    # ... success path ...
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except InvalidServerVersion:
                    errors["base"] = "invalid_server_version"
                except MusicAssistantClientException:
                    LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(...)
        # ...
        ```
    *   The `get_server_info` function attempts to establish a connection and retrieve server information using the `MusicAssistantClient`:
        ```python
        # homeassistant/components/music_assistant/config_flow.py
        async def get_server_info(hass: HomeAssistant, url: str) -> ServerInfoMessage:
            """Validate the user input allows us to connect."""
            async with MusicAssistantClient(
                url, aiohttp_client.async_get_clientsession(hass)
            ) as client:
                if TYPE_CHECKING:
                    assert client.server_info is not None
                return client.server_info
        ```
        The `async with MusicAssistantClient(...)` block implicitly calls the client's connection and initial data fetching logic (likely in its `__aenter__` method). This serves as the "test call".
    *   If `MusicAssistantClient` fails to connect (e.g., wrong URL, server down, network issue), it raises `CannotConnect`. If the server version is incompatible, it raises `InvalidServerVersion`.
    *   These specific exceptions are caught in `async_step_user`, and `errors["base"]` is populated. This results in an error message being displayed to the user on the configuration form, allowing them to correct the input. This matches the pattern recommended by the rule.

2.  **Zeroconf-discovered configuration (`async_step_zeroconf`):**
    When a Music Assistant server is discovered via Zeroconf:
    *   The `async_step_zeroconf` method also validates the connection to the discovered server URL using the same `get_server_info` helper function:
        ```python
        # homeassistant/components/music_assistant/config_flow.py
        async def async_step_zeroconf(
            self, discovery_info: ZeroconfServiceInfo
        ) -> ConfigFlowResult:
            # ...
            try:
                await get_server_info(self.hass, self.server_info.base_url)
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")
            return await self.async_step_discovery_confirm()
        ```
    *   If `get_server_info` raises `CannotConnect`, the flow is aborted with a "cannot_connect" reason. This is an appropriate way to handle a failed connection test for a discovered instance, as the URL was not directly input by the user in this step.

Both configuration paths (manual and discovery) include a connection test before finalizing the configuration entry, and user-facing errors are provided in the manual flow.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:04:40. Prompt tokens: 30324, Output tokens: 1125, Total tokens: 34130_
