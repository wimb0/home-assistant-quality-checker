# overkiz: inject-websession

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [inject-websession](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `inject-websession` rule applies to the `overkiz` integration because it communicates with an external service or local hub over HTTP, which is managed by its dependency, `pyoverkiz`. The integration is expected to provide an `aiohttp.ClientSession` or an `httpx.AsyncClient` to its underlying library.

The `overkiz` integration correctly follows this rule. It creates and injects an `aiohttp.ClientSession` into the `pyoverkiz.client.OverkizClient` in all relevant places:

1.  **During setup for local API connections (`__init__.py`):**
    The `create_local_client` function explicitly creates a new `aiohttp.ClientSession` using `async_create_clientsession` and passes it to the `OverkizClient`.
    ```python
    # homeassistant/components/overkiz/__init__.py
    def create_local_client(
        hass: HomeAssistant, host: str, token: str, verify_ssl: bool
    ) -> OverkizClient:
        """Create Overkiz local client."""
        session = async_create_clientsession(hass, verify_ssl=verify_ssl) #highlight

        return OverkizClient(
            username="",
            password="",
            token=token,
            session=session, #highlight
            server=generate_local_server(host=host),
            verify_ssl=verify_ssl,
        )
    ```

2.  **During setup for cloud API connections (`__init__.py`):**
    The `create_cloud_client` function also creates a new `aiohttp.ClientSession` using `async_create_clientsession`. A comment in the code (`# To allow users with multiple accounts/hubs, we create a new session so they have separate cookies`) justifies creating a new session, which is an allowed exception by the rule.
    ```python
    # homeassistant/components/overkiz/__init__.py
    def create_cloud_client(
        hass: HomeAssistant, username: str, password: str, server: OverkizServer
    ) -> OverkizClient:
        """Create Overkiz cloud client."""
        # To allow users with multiple accounts/hubs, we create a new session so they have separate cookies
        session = async_create_clientsession(hass) #highlight

        return OverkizClient(
            username=username, password=password, session=session, server=server #highlight
        )
    ```

3.  **During config flow validation (`config_flow.py`):**
    The `async_validate_input` method in the config flow similarly creates and passes a session to `OverkizClient` for both local and cloud API types.
    ```python
    # homeassistant/components/overkiz/config_flow.py
    async def async_validate_input(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Validate user credentials."""
        # ...
        if self._api_type == APIType.LOCAL:
            # ...
            session = async_create_clientsession( #highlight
                self.hass, verify_ssl=user_input[CONF_VERIFY_SSL]
            )
            client = OverkizClient(
                # ...
                session=session, #highlight
                # ...
            )
        else:  # APIType.CLOUD
            session = async_create_clientsession(self.hass) #highlight
            client = OverkizClient(
                # ...
                session=session, #highlight
                # ...
            )
        # ...
    ```

In all instances, the integration uses `async_create_clientsession`, which is explicitly allowed by the rule, especially when a shared session is not desirable (e.g., due to cookie management or specific SSL configurations). The `pyoverkiz` library's `OverkizClient` accepts a `session` parameter, indicating it supports this injection.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:49:13. Prompt tokens: 86898, Output tokens: 1026, Total tokens: 90559_
