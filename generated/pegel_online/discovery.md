```markdown
# pegel_online: discovery

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [discovery](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery)                                                     |
| Status | **exempt**                                                               |
| Reason | The integration connects to a cloud service to retrieve data for physical stations, which are not discoverable on the local network. |

## Overview

The `discovery` rule encourages integrations to leverage network protocols or other methods (like mDNS, SSDP, Bluetooth) to automatically find devices or services on the user's local network. This improves user experience by simplifying setup.

However, the `pegel_online` integration connects to the public PEGELONLINE web service (a cloud API) to retrieve water level and related data for specific measuring stations located at various physical locations. The configuration process involves the user providing a location and radius, after which the integration queries the remote API to find relevant stations within that area.

This type of interaction with a remote cloud service providing data for physical locations is fundamentally different from discovering devices or services present on the user's local network. The concept of local network discovery protocols (mDNS, SSDP, etc.) does not apply to fetching data for remote stations via a web API.

Looking at the code:
*   The `manifest.json` (`homeassistant/components/pegel_online/manifest.json`) does not list any discovery mechanisms like `zeroconf`, `ssdp`, or `bluetooth`.
*   The `config_flow.py` (`homeassistant/components/pegel_online/config_flow.py`) implements `async_step_user` and `async_step_select_station`. The `async_step_user` prompts for a location and radius, and then calls `api.async_get_nearby_stations` to find stations via the remote API. It does not contain steps for processing local network discovery information like `async_step_zeroconf` or `async_step_ssdp`.

Since the integration interacts solely with a cloud service for data retrieval based on user-defined location parameters, rather than discovering local network entities, the `discovery` rule does not apply. The integration is correctly categorized as `iot_class: cloud_polling` in its manifest, which aligns with its nature.

```

_Created at 2025-05-25 11:24:20. Prompt tokens: 6475, Output tokens: 543, Total tokens: 7685_
