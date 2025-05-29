# nest: inject-websession

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [inject-websession](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `inject-websession` rule applies to the `nest` integration because it communicates with Google's cloud services (Smart Device Management API, Pub/Sub API) over HTTP, facilitated by its `google-nest-sdm` dependency.

The integration **fully follows** this rule. The primary mechanism for HTTP communication within the `google-nest-sdm` library is through an authentication handler (a class inheriting from `google_nest_sdm.auth.AbstractAuth`). The Nest integration ensures that this authentication handler is provided with a Home Assistant-managed `aiohttp.ClientSession`.

Key evidence is found in `homeassistant/components/nest/api.py`:

1.  **Authentication Handlers Receive Injected Session:**
    *   The `AsyncConfigEntryAuth` class, which is used for the main OAuth flow, is initialized with a `websession`:
        ```python
        # homeassistant/components/nest/api.py
        class AsyncConfigEntryAuth(AbstractAuth):
            def __init__(
                self,
                websession: ClientSession,  # <--- Receives aiohttp.ClientSession
                oauth_session: config_entry_oauth2_flow.OAuth2Session,
                client_id: str,
                client_secret: str,
            ) -> None:
                super().__init__(websession, API_URL) # <--- Passed to google_nest_sdm.AbstractAuth
                # ...
        ```
    *   Similarly, `AccessTokenAuthImpl`, used during config flow or for specific operations, also accepts and passes on a `websession`:
        ```python
        # homeassistant/components/nest/api.py
        class AccessTokenAuthImpl(AbstractAuth):
            def __init__(
                self,
                websession: ClientSession, # <--- Receives aiohttp.ClientSession
                access_token: str,
                host: str,
            ) -> None:
                super().__init__(websession, host) # <--- Passed to google_nest_sdm.AbstractAuth
                # ...
        ```

2.  **Session Provisioning using `async_get_clientsession`:**
    *   When these authentication handlers are instantiated, the integration correctly uses `aiohttp_client.async_get_clientsession(hass)` to obtain the shared Home Assistant `aiohttp.ClientSession`.
    *   In `new_auth()`:
        ```python
        # homeassistant/components/nest/api.py
        async def new_auth(hass: HomeAssistant, entry: NestConfigEntry) -> AbstractAuth:
            # ...
            return AsyncConfigEntryAuth(
                aiohttp_client.async_get_clientsession(hass), # <--- Injected here
                # ...
            )
        ```
    *   In `new_subscriber_with_token()`:
        ```python
        # homeassistant/components/nest/api.py
        def new_subscriber_with_token(...):
            return GoogleNestSubscriber(
                AccessTokenAuthImpl(
                    aiohttp_client.async_get_clientsession(hass), # <--- Injected here
                    # ...
                ),
                # ...
            )
        ```
    *   In `new_pubsub_admin_client()`:
        ```python
        # homeassistant/components/nest/api.py
        def new_pubsub_admin_client(...):
            return AdminClient(
                auth=AccessTokenAuthImpl(
                    aiohttp_client.async_get_clientsession(hass), # <--- Injected here
                    # ...
                ),
                # ...
            )
        ```

3.  **Dependency Clients Use Auth Handlers:**
    *   The actual clients from the `google-nest-sdm` library, such as `GoogleNestSubscriber` and `AdminClient`, are then initialized with these `auth` objects (e.g., instances of `AsyncConfigEntryAuth` or `AccessTokenAuthImpl`).
    *   Since these `auth` objects encapsulate the injected `aiohttp.ClientSession`, all HTTP requests made by the `google-nest-sdm` dependency leverage the Home Assistant-managed session. This fulfills the rule's requirement to pass a web session to the dependency client.

This pattern ensures efficient use of web sessions by reusing Home Assistant's managed `aiohttp.ClientSession`.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:18:26. Prompt tokens: 32258, Output tokens: 1084, Total tokens: 35977_
