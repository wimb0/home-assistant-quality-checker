```markdown
# pegel_online: inject-websession

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [inject-websession](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession)                                                     |
| Status | **done**                                       |

## Overview

The `inject-websession` rule requires integrations that make HTTP requests to support passing in a Home Assistant managed web session (`aiohttp.ClientSession` or `httpx.AsyncClient`) to their dependency client. This promotes efficient use of network resources.

The `pegel_online` integration uses the `aiopegelonline` library (as specified in `manifest.json`) to interact with the PEGELONLINE service via HTTP, confirmed by its `cloud_polling` iot_class. Therefore, this rule is applicable.

The integration fully follows this rule. It correctly obtains a shared `aiohttp.ClientSession` from Home Assistant using `async_get_clientsession(hass)` and passes this session to the `aiopegelonline.PegelOnline` client when initializing it.

Specifically:

*   In `homeassistant/components/pegel_online/__init__.py`, the `PegelOnline` client is initialized in `async_setup_entry` with `api = PegelOnline(async_get_clientsession(hass))`. This injected client instance is then passed to the `PegelOnlineDataUpdateCoordinator`.
*   In `homeassistant/components/pegel_online/config_flow.py`, the `PegelOnline` client is initialized in `async_step_user` with `api = PegelOnline(async_get_clientsession(self.hass))` to fetch nearby stations.

This pattern ensures that the integration leverages Home Assistant's shared web session, adhering to the `inject-websession` rule.

## Suggestions

No suggestions needed. The integration correctly implements the `inject-websession` rule.
```

_Created at 2025-05-25 11:26:28. Prompt tokens: 5794, Output tokens: 468, Total tokens: 7080_
