```markdown
# fritzbox: async-dependency

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [async-dependency](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/async-dependency) |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `async-dependency` rule encourages integrations to use asynchronous libraries to align with Home Assistant's asyncio event loop, improving performance and code neatness. This rule is applicable to the `fritzbox` integration as it relies on an external library for communication.

The `fritzbox` integration uses the `pyfritzhome` library, as specified in the `manifest.json`. `pyfritzhome` is a synchronous library that uses the `requests` library for making HTTP calls.

While the integration correctly handles the synchronous nature of `pyfritzhome` by offloading I/O-bound calls to the executor thread pool using `hass.async_add_executor_job` (seen extensively in `coordinator.py`, `config_flow.py`, `__init__.py`, and various platform files like `cover.py`, `switch.py`, `light.py`, `climate.py`, `button.py`), the underlying dependency itself (`pyfritzhome`) is not asynchronous.

The rule states that "ideally, your library should also use asyncio". Since the core dependency is synchronous, the integration does not fully meet this ideal state described by the rule, even though it correctly uses `async_add_executor_job` to mitigate the impact. Therefore, the integration is marked as "todo" for this rule.

Examples of using `hass.async_add_executor_job` to handle synchronous calls:

*   In `coordinator.py`: `await self.hass.async_add_executor_job(self.fritz.login)`
*   In `cover.py`: `await self.hass.async_add_executor_job(self.data.set_blind_open, True)`
*   In `config_flow.py`: `await self.hass.async_add_executor_job(self._try_connect)`

This pattern is consistently applied for all I/O operations with `pyfritzhome`. However, the dependency itself remains synchronous.

## Suggestions

To fully comply with the `async-dependency` rule, the `pyfritzhome` library should be refactored to be asynchronous. This would involve:

1.  Changing the library's internal HTTP communication from `requests` (synchronous) to an asynchronous library like `aiohttp`.
2.  Updating the methods within `pyfritzhome` that perform I/O to be `async def` functions.
3.  Once `pyfritzhome` is asynchronous, the `fritzbox` integration code can be updated to directly `await` calls to the library methods instead of wrapping them in `hass.async_add_executor_job`.

This refactoring would eliminate the need for thread pool offloading for this dependency, resulting in more efficient and cleaner code within the integration, aligning with the rule's objective.

```python
# Example of current code using executor job (e.g., in cover.py)
async def async_open_cover(self, **kwargs: Any) -> None:
    """Open the cover."""
    await self.hass.async_add_executor_job(self.data.set_blind_open, True)
    await self.coordinator.async_refresh() # Coordinator also uses executor

# Example of how it could look if pyfritzhome were async (assuming set_blind_open was async)
# Note: The coordinator update would also need to be async
async def async_open_cover(self, **kwargs: Any) -> None:
    """Open the cover."""
    await self.data.set_blind_open(True) # Direct await
    await self.coordinator.async_refresh() # Should ideally also be async calls internally
```

The primary suggestion is to work towards making the `pyfritzhome` dependency itself asynchronous.
```

_Created at 2025-05-25 11:38:15. Prompt tokens: 18677, Output tokens: 939, Total tokens: 21030_
