```markdown
# samsungtv: async-dependency

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [async-dependency](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/async-dependency)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that integrations either use asynchronous libraries for their dependencies or, if using synchronous libraries, correctly offload synchronous calls to the executor to prevent blocking the Home Assistant event loop.

The `samsungtv` integration utilizes several external libraries: `samsungctl`, `samsungtvws`, `getmac`, `wakeonlan`, and `async-upnp-client`.

Upon reviewing the code:

1.  **Asynchronous Libraries (`samsungtvws`, `async-upnp-client`)**: The integration correctly uses the asynchronous APIs provided by these libraries.
    *   In `bridge.py`, `SamsungTVWSAsyncRemote`, `SamsungTVEncryptedWSAsyncRemote`, and `SamsungTVAsyncRest` (from `samsungtvws`) are used with `async def` methods and `await` calls (e.g., `async_try_connect`, `async_device_info`, `async_send_commands`).
    *   In `media_player.py`, `async_upnp_client` is used for DMR functionality with `async def` methods and `await` (e.g., `async_create_device`, `async_subscribe_services`, `async_set_volume_level`).
2.  **Synchronous Libraries (`samsungctl`, `getmac`, `wakeonlan`)**: The integration correctly identifies the synchronous nature of these libraries and offloads their execution to Home Assistant's executor using `hass.async_add_executor_job`.
    *   In `bridge.py`, the `SamsungTVLegacyBridge` class, which uses `samsungctl`, explicitly wraps synchronous calls like `_is_on`, `_try_connect`, `_send_key`, and `_close_remote` within `await self.hass.async_add_executor_job(...)`.
    *   In `__init__.py` and `config_flow.py`, calls to `getmac.get_mac_address` are wrapped in `await self.hass.async_add_executor_job(...)`.
    *   In `entity.py`, the call to `wakeonlan.send_magic_packet` in `_wake_on_lan` is offloaded via `await self.hass.async_add_executor_job(self._wake_on_lan)`.

By using asynchronous APIs for async dependencies and properly offloading synchronous calls, the integration ensures that it does not block the Home Assistant event loop. Thus, the integration fully follows the `async-dependency` rule.

## Suggestions

No suggestions needed. The integration correctly handles both synchronous and asynchronous dependencies.
```

_Created at 2025-05-25 11:33:23. Prompt tokens: 29820, Output tokens: 682, Total tokens: 31571_
