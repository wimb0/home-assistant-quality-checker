# wled: async-dependency

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [async-dependency](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/async-dependency)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `async-dependency` rule requires that external libraries used by an integration are asyncio-native to ensure efficient operation within Home Assistant's asyncio event loop.

This rule applies to the `wled` integration as it utilizes an external Python library, `wled`, specified in its `manifest.json` file:
```json
"requirements": ["wled==0.21.0"],
```

The `wled` integration correctly follows this rule. The `wled` Python library (version 0.21.0) is designed to be asynchronous. This is evident from its usage within the integration:

1.  **Initialization with `aiohttp.ClientSession`**:
    In `coordinator.py`, both `WLED` and `WLEDReleases` objects (from the `wled` library) are initialized with an `aiohttp.ClientSession` obtained via `async_get_clientsession(hass)`. This is a standard practice for asyncio-based HTTP client libraries.
    ```python
    # coordinator.py
    from wled import WLED, WLEDReleases
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    # ...
    class WLEDDataUpdateCoordinator(DataUpdateCoordinator[WLEDDevice]):
        def __init__(self, hass: HomeAssistant, *, entry: ConfigEntry) -> None:
            # ...
            self.wled = WLED(entry.data[CONF_HOST], session=async_get_clientsession(hass))
            # ...

    class WLEDReleasesDataUpdateCoordinator(DataUpdateCoordinator[Releases]):
        def __init__(self, hass: HomeAssistant) -> None:
            # ...
            self.wled = WLEDReleases(session=async_get_clientsession(hass))
            # ...
    ```
    The same pattern is used in `config_flow.py`:
    ```python
    # config_flow.py
    async def _async_get_device(self, host: str) -> Device:
        session = async_get_clientsession(self.hass)
        wled = WLED(host, session=session)
        return await wled.update()
    ```

2.  **Asynchronous Methods**:
    All interactions with the `wled` library that involve I/O operations (e.g., fetching data, sending commands) are performed using `async def` methods and `await` calls. This indicates that the library's methods are coroutines.
    Examples:
    *   `await self.wled.update()` in `coordinator.py` and `config_flow.py`.
    *   `await self.wled.connect()`, `await self.wled.listen(...)`, `await self.wled.disconnect()` in `coordinator.py`.
    *   `await self.coordinator.wled.upgrade(...)` in `update.py`.
    *   `await self.coordinator.wled.master(...)`, `await self.coordinator.wled.segment(...)` in `light.py`.
    *   `await self.coordinator.wled.reset()` in `button.py`.
    *   And many other similar calls throughout the entity platform files (`number.py`, `select.py`, `switch.py`).

The integration consistently uses `async` and `await` when interacting with the `wled` library, ensuring that operations are non-blocking and integrate well with Home Assistant's event loop. This adheres to the `async-dependency` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 23:08:56. Prompt tokens: 20117, Output tokens: 903, Total tokens: 22486_
