```markdown
# fritzbox: inject-websession

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [inject-websession](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession) |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The rule `inject-websession` requires that integrations making HTTP requests should utilize an asynchronous web session provided by Home Assistant, typically using `aiohttp` or `httpx`, and passing that session into their dependency client. This improves efficiency by allowing sessions to be shared.

The `fritzbox` integration uses the `pyfritzhome` library to communicate with the FRITZ!Box device. The code analysis reveals that `pyfritzhome` is treated as a blocking dependency. In `homeassistant/components/fritzbox/coordinator.py` and `homeassistant/components/fritzbox/config_flow.py`, calls to `pyfritzhome.Fritzhome` methods like `login`, `update_devices`, `update_templates`, `get_device_elements`, and `logout` are wrapped in `await self.hass.async_add_executor_job(...)`. This indicates that `pyfritzhome` performs synchronous I/O, likely using a synchronous HTTP library like `requests` (which is a typical dependency for libraries treated this way).

Since the integration relies on a synchronous library that doesn't expose an interface to inject an asynchronous Home Assistant managed session, it does not currently comply with the `inject-websession` rule. The rule applies because the integration fundamentally makes HTTP requests, albeit through a synchronous dependency.

## Suggestions

To comply with the `inject-websession` rule, the `fritzbox` integration would need to switch to an asynchronous dependency for making HTTP requests or update the existing `pyfritzhome` library to support asynchronous operations and accept an `aiohttp` or `httpx` session.

1.  **Update/Fork `pyfritzhome`:** The most direct path is to contribute to the `pyfritzhome` library or create a fork that replaces its synchronous HTTP calls (presumably using `requests`) with asynchronous calls using `aiohttp`. The library's main client class (`Fritzhome`) would need to accept an `aiohttp.ClientSession` instance during initialization.
2.  **Modify Integration:** Once the `pyfritzhome` library supports asynchronous operations and session injection:
    *   Remove `pyfritzhome` from `requirements` in `manifest.json` and add it as a custom dependency if forked, or update the version if upstream adds support.
    *   In `homeassistant/components/fritzbox/coordinator.py`, modify the instantiation of `Fritzhome`:
        ```python
        # Before:
        self.fritz = Fritzhome(
            host=self.config_entry.data[CONF_HOST],
            user=self.config_entry.data[CONF_USERNAME],
            password=self.config_entry.data[CONF_PASSWORD],
        )

        # After (assuming pyfritzhome supports it):
        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        session = async_get_clientsession(hass)
        self.fritz = Fritzhome(
            host=self.config_entry.data[CONF_HOST],
            user=self.config_entry.data[CONF_USERNAME],
            password=self.config_entry.data[CONF_PASSWORD],
            session=session, # Pass the session
        )
        ```
    *   Similarly, update the `_try_connect` method in `homeassistant/components/fritzbox/config_flow.py` to create and pass a session.
    *   Crucially, remove all `await self.hass.async_add_executor_job(...)` calls used for API interaction methods (`self.fritz.login`, `self.fritz.update_devices`, etc.) and instead `await` the corresponding methods directly, as they would now be asynchronous:
        ```python
        # Before (in async_setup):
        await self.hass.async_add_executor_job(self.fritz.login)

        # After:
        await self.fritz.login() # Assuming login is now async
        ```
        Apply this change to all methods in `coordinator.py`, `config_flow.py`, and any platform files that make direct calls wrapped in `async_add_executor_job`.
    *   Ensure error handling is updated to catch exceptions from the asynchronous library (`aiohttp.ClientError` etc.).

This process involves a significant update to the underlying library used by the integration.
```

_Created at 2025-05-25 11:38:26. Prompt tokens: 18889, Output tokens: 1083, Total tokens: 21078_
