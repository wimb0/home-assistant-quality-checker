# wled: inject-websession

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [inject-websession](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `inject-websession` rule requires that integrations making HTTP requests support passing a Home Assistant-managed web session (`aiohttp.ClientSession` or `httpx.AsyncClient`) to their underlying HTTP client library. This improves efficiency by reusing sessions.

The `wled` integration interacts with WLED devices, which are controlled over HTTP, and also fetches release information from GitHub (which is also an HTTP request). Therefore, this rule applies.

The integration correctly follows this rule:

1.  **Device Communication:**
    In `coordinator.py`, the `WLEDDataUpdateCoordinator` initializes the `WLED` client (from the `wled` library) by passing it a session obtained via `async_get_clientsession(hass)`:
    ```python
    # coordinator.py
    class WLEDDataUpdateCoordinator(DataUpdateCoordinator[WLEDDevice]):
        # ...
        def __init__(
            self,
            hass: HomeAssistant,
            *,
            entry: ConfigEntry,
        ) -> None:
            """Initialize global WLED data updater."""
            # ...
            self.wled = WLED(entry.data[CONF_HOST], session=async_get_clientsession(hass)) # Correct usage
            # ...
    ```

2.  **Release Information Fetching:**
    Similarly, in `coordinator.py`, the `WLEDReleasesDataUpdateCoordinator` initializes the `WLEDReleases` client by passing it a session from `async_get_clientsession(hass)`:
    ```python
    # coordinator.py
    class WLEDReleasesDataUpdateCoordinator(DataUpdateCoordinator[Releases]):
        """Class to manage fetching WLED releases."""

        def __init__(self, hass: HomeAssistant) -> None:
            """Initialize global WLED releases updater."""
            self.wled = WLEDReleases(session=async_get_clientsession(hass)) # Correct usage
            # ...
    ```

3.  **Configuration Flow:**
    During the configuration flow, in `config_flow.py`, when validating the connection to a WLED device, a Home Assistant-managed session is also used:
    ```python
    # config_flow.py
    class WLEDFlowHandler(ConfigFlow, domain=DOMAIN):
        # ...
        async def _async_get_device(self, host: str) -> Device:
            """Get device information from WLED device."""
            session = async_get_clientsession(self.hass) # Correct usage
            wled = WLED(host, session=session)
            return await wled.update()
    ```

In all relevant instances where HTTP requests are initiated through the `wled` library, the integration correctly injects the `aiohttp.ClientSession` provided by Home Assistant. This ensures efficient use of web sessions.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 23:09:14. Prompt tokens: 20947, Output tokens: 749, Total tokens: 22669_
