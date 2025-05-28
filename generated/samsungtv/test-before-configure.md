```markdown
# samsungtv: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

This rule requires integrations that connect to a device or service to test the connection during the configuration flow *before* completing the setup. This helps the user identify and resolve connectivity issues early.

The `samsungtv` integration applies to this rule as it connects to Samsung TVs via the network.

The integration fully follows this rule. The configuration flow (`homeassistant/components/samsungtv/config_flow.py`) includes explicit steps to test the connection and identify the appropriate connection method and device information before allowing the user to complete the flow or proceeding to pairing steps.

Specifically, the `async_step_user` and subsequent discovery steps (`async_step_ssdp`, `async_step_dhcp`, `async_step_zeroconf`) call `self._async_set_name_host_from_input` (which resolves the hostname) and then `await self._async_create_bridge()`.

Inside `_async_create_bridge`, the crucial call `await self._async_get_device_info_and_method()` is made. This function, implemented across `config_flow.py` and `bridge.py`, attempts to connect to the TV using different ports and methods (WebSocket, Encrypted WebSocket, Legacy) via the `SamsungTVWSAsyncRemote`, `SamsungTVEncryptedWSAsyncRemote`, and `samsungctl.Remote` libraries. It catches various connection-related exceptions (`ConnectionFailure`, `OSError`, `AsyncioTimeoutError`, `UnauthorizedError`, `ConnectionClosedError`, `WebSocketException`, `AccessDenied`, `UnhandledResponse`) and translates them into specific result codes like `RESULT_CANNOT_CONNECT`, `RESULT_NOT_SUPPORTED`, and `RESULT_AUTH_MISSING` (see `homeassistant/components/samsungtv/const.py`).

If `_async_get_device_info_and_method` returns a result that is not in `SUCCESSFUL_RESULTS` (meaning it's not `RESULT_SUCCESS` or `RESULT_AUTH_MISSING`), the `_async_create_bridge` function raises an `AbortFlow` with the corresponding result code. This aborts the flow and presents an error message to the user (e.g., "cannot_connect", "not_supported").

If the result is `RESULT_AUTH_MISSING`, the flow proceeds to the `async_step_pairing` or `async_step_encrypted_pairing` steps, where further specific connection tests (like prompting for PIN or waiting for TV authorization) are performed, and errors are handled by showing the form again with an error message (`RESULT_AUTH_MISSING`, `RESULT_INVALID_PIN`).

This process correctly validates the connection using the provided host information before proceeding to the final configuration step, thereby adhering to the `test-before-configure` rule.

## Suggestions

No suggestions needed. The integration already follows the rule.
```

_Created at 2025-05-25 11:28:53. Prompt tokens: 30343, Output tokens: 738, Total tokens: 32054_
