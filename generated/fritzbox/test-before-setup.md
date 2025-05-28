```markdown
# fritzbox: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup) |
| Status | **done**                                                                 |

## Overview

This rule requires integrations to check for connectivity and authentication issues during the `async_setup_entry` phase and raise appropriate `ConfigEntry` exceptions. The `fritzbox` integration follows this rule.

The primary logic for initial connection and setup testing resides within the `FritzboxDataUpdateCoordinator.async_setup` method (`homeassistant/components/fritzbox/coordinator.py`). The `async_setup_entry` function in `__init__.py` calls `await coordinator.async_setup()` before forwarding platforms, ensuring that the necessary checks happen upfront.

Within `FritzboxDataUpdateCoordinator.async_setup`:

1.  A `Fritzhome` object is instantiated with the provided host, username, and password.
2.  It attempts to `login()` to the FRITZ!Box via `self.hass.async_add_executor_job(self.fritz.login)`.
3.  This login attempt is wrapped in a `try...except` block.
4.  `requests.exceptions.RequestConnectionError` is caught, and `ConfigEntryNotReady` is raised, indicating a temporary issue like the device being offline.
5.  `pyfritzhome.LoginError` is caught, and `ConfigEntryAuthFailed` is raised, indicating incorrect credentials.

These explicit checks and the raising of the required exceptions satisfy the core requirement of the `test-before-setup` rule by verifying the connection and authentication status before the integration is fully set up and platforms are loaded. The integration also uses `await self.async_config_entry_first_refresh()`, which further validates communication by fetching initial data, and its error handling (`UpdateFailed` or subsequent `ConfigEntryAuthFailed` on re-login failure) is also appropriate for the setup phase.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:20:59. Prompt tokens: 19043, Output tokens: 507, Total tokens: 20369_
