```markdown
# samsungtv: inject-websession

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [inject-websession](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession)                                                     |
| Status | **todo**                                                                 |

## Overview

This rule requires integrations making HTTP requests via `aiohttp` or `httpx` to inject a shared `ClientSession` or `AsyncClient` obtained from Home Assistant helpers (`async_get_clientsession`, `get_async_client`). This improves efficiency by reusing connections.

The `samsungtv` integration interacts with Samsung TVs using various protocols (legacy, websocket, encrypted websocket) which involve network communication, including HTTP/HTTPS requests (e.g., for REST API calls and potentially initial handshakes or UPnP discovery). Therefore, the rule applies to this integration.

The integration partially follows the rule.

*   The `SamsungTVAsyncRest` class, used by `SamsungTVWSBridge` and `SamsungTVEncryptedBridge` for REST API calls, correctly receives a session via `async_get_clientsession(self.hass)` as seen in `bridge.py`:
    ```python
    # bridge.py, SamsungTVWSBridge.async_device_info
    self._rest_api = SamsungTVAsyncRest(
        host=self.host,
        session=async_get_clientsession(self.hass),
        port=self.port,
        timeout=TIMEOUT_WEBSOCKET,
    )
    ```
    ```python
    # bridge.py, SamsungTVEncryptedBridge.async_device_info
    rest_api = SamsungTVAsyncRest(
        host=self.host,
        session=async_get_clientsession(self.hass),
        port=rest_api_port,
        timeout=TIMEOUT_WEBSOCKET,
    )
    ```
*   The `SamsungTVEncryptedWSAsyncRemote` used by `SamsungTVEncryptedBridge` correctly receives a session:
    ```python
    # bridge.py, SamsungTVEncryptedBridge._async_get_remote_under_lock
    self._remote = SamsungTVEncryptedWSAsyncRemote(
        host=self.host,
        port=self.port,
        web_session=async_get_clientsession(self.hass), # Session injected here
        token=self.token or "",
        session_id=self.session_id or "",
        timeout=TIMEOUT_WEBSOCKET,
    )
    ```
*   The `async_upnp_client` dependency used in `media_player.py` for DMR functionality correctly uses `AiohttpSessionRequester` initialized with `async_get_clientsession(self.hass)`:
    ```python
    # media_player.py, SamsungTVDevice._async_startup_dmr
    session = async_get_clientsession(self.hass)
    upnp_requester = AiohttpSessionRequester(session)
    upnp_factory = UpnpFactory(upnp_requester, non_strict=True)
    ```
*   However, the `SamsungTVWSAsyncRemote` class used by `SamsungTVWSBridge` does not appear to accept a `web_session` argument in its constructor or `start_listening` method according to the usage in `bridge.py`. This suggests it might create its own internal session, which would violate the rule.
    ```python
    # bridge.py, SamsungTVWSBridge._async_get_remote_under_lock
    self._remote = SamsungTVWSAsyncRemote(
        host=self.host,
        port=self.port,
        token=self.token,
        timeout=TIMEOUT_WEBSOCKET,
        name=VALUE_CONF_NAME,
    ) # No session argument passed
    ```
*   The `SamsungTVLegacyBridge` uses `samsungctl.Remote`, which is likely a blocking library and does not use `aiohttp` or `httpx`, so session injection as described in the rule may not be applicable to this specific library.

Because the `SamsungTVWSAsyncRemote` connection part does not seem to inject a shared session, the integration does not fully comply with the rule.

## Suggestions

To make the integration fully compliant, investigate the `samsungtvws` library, specifically the `SamsungTVWSAsyncRemote` class.

1.  **Check `samsungtvws` library:** Determine if `SamsungTVWSAsyncRemote` supports accepting an `aiohttp.ClientSession` instance during initialization or when starting the connection.
2.  **Modify `SamsungTVWSBridge`:**
    *   If the library supports it, update the `SamsungTVWSBridge._async_get_remote_under_lock` method to fetch `async_get_clientsession(self.hass)` and pass it to the `SamsungTVWSAsyncRemote` constructor.
    *   If the library does not support it, consider contributing the functionality to the upstream `samsungtvws` library or creating a wrapper within the integration that manages session injection if possible.

Making this change will ensure that the websocket connections for newer TVs also benefit from shared session efficiency, aligning with the `inject-websession` rule.
```

_Created at 2025-05-25 11:33:38. Prompt tokens: 30032, Output tokens: 1199, Total tokens: 32949_
