```markdown
# samsungtv: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/)       |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that an integration verifies its ability to set up correctly during the `async_setup_entry` phase, providing immediate feedback to the user by raising appropriate `ConfigEntry` exceptions for failure conditions (e.g., temporary offline, invalid authentication, permanent error).

The `samsungtv` integration follows this rule.

The primary mechanism used by the integration to check connectivity and authentication status during setup is through the data update coordinator. The `async_setup_entry` function in `homeassistant/components/samsungtv/__init__.py` initializes the `SamsungTVDataUpdateCoordinator` and then calls `await coordinator.async_config_entry_first_refresh()`.

As noted in the rule description, utilizing `await coordinator.async_config_entry_first_refresh()` is an acceptable implicit implementation of this rule. The coordinator's `_async_update_data` method (in `homeassistant/components/samsungtv/coordinator.py`) calls `self.bridge.async_is_on()`. The bridge's `async_is_on()` method, in turn, attempts to establish a connection via `_async_get_remote()` and `_async_get_remote_under_lock()` methods (in `homeassistant/components/samsungtv/bridge.py`).

These bridge methods (`_async_get_remote_under_lock`) handle various exceptions:
*   `UnauthorizedError`: Caught and handled specifically by calling `self._notify_reauth_callback()`, which triggers a reauthentication flow via `entry.async_start_reauth(hass)` in `__init__.py`. This correctly aligns with the rule's requirement to handle authentication failures.
*   `ConnectionClosedError`, `ConnectionFailure`, `WebSocketException`, `AsyncioTimeoutError`, `OSError`: Caught and result in the remote object being set to `None`. The `async_is_on` check will then return `False`. When this happens during the `async_config_entry_first_refresh`, Home Assistant will raise `ConfigEntryNotReady`, indicating a temporary issue and prompting a retry.

Additionally, `async_setup_entry` includes an explicit check for missing `CONF_TOKEN` or `CONF_SESSION_ID` when using the `METHOD_ENCRYPTED_WEBSOCKET`, immediately raising `ConfigEntryAuthFailed` if these required credentials are not present.

While the integration could potentially check for "not supported" conditions identified during the config flow's device info retrieval (`async_get_device_info` in `bridge.py`) and raise `ConfigEntryError` in `async_setup_entry`, the current reliance on the coordinator's initial refresh and the explicit auth check fulfill the core requirements of this quality scale rule.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:29:05. Prompt tokens: 30186, Output tokens: 720, Total tokens: 32676_
