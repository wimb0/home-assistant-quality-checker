```markdown
# pegel_online: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info)                                                     |
| Status | **exempt**                                                               |
| Reason | The integration interacts with a cloud API and does not use local network discovery protocols that provide device network addresses requiring updates. |

## Overview

The `discovery-update-info` rule requires integrations that use network discovery (like mDNS, DHCP, or SSDP) to locate local devices or services to handle potential changes in their network addresses (like IP addresses) by updating the stored information during subsequent discovery events. This prevents the integration from losing connection to a device if its IP address changes dynamically.

Looking at the `pegel_online` integration's code, specifically `manifest.json`, `config_flow.py`, and `__init__.py`:

*   The `manifest.json` does not declare any local network discovery methods like `zeroconf`, `dhcp`, or `ssdp`.
*   The `config_flow.py` implements user-initiated configuration based on searching for stations by location and radius, not local network discovery.
*   The `__init__.py` uses `aiohttp_client.async_get_clientsession` to interact with a cloud API (`pegelonline.info`) via the `aiopegelonline` library, connecting based on a station's UUID obtained during the config flow search.

This integration interacts with a cloud service (`pegelonline.info`) to retrieve data for specific water measuring stations, which are identified by a unique UUID. It does not discover local network devices or services that would have dynamically changing IP addresses on the user's network. Therefore, the core premise of the `discovery-update-info` rule – maintaining connectivity to a local device despite network address changes via discovery updates – does not apply to this integration.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:24:26. Prompt tokens: 6076, Output tokens: 483, Total tokens: 7050_
