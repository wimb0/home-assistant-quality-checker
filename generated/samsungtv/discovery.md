```markdown
# samsungtv: discovery

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [discovery](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `discovery` rule requires that integrations for devices capable of being discovered implement appropriate discovery methods to ease setup for users. This integration, `samsungtv`, is for Samsung Smart TVs, which are network-connected devices typically discoverable via various protocols.

Based on the provided code, the `samsungtv` integration fully implements discovery:

1.  **`manifest.json`**: The manifest file explicitly declares support for multiple discovery methods:
    *   `ssdp`: It lists several Service Types (`st`) related to Samsung UPnP services (`urn:samsung.com:device:RemoteControlReceiver:1`, `urn:samsung.com:service:MainTVAgent2:1`, `urn:schemas-upnp-org:service:RenderingControl:1`) and filters by manufacturer ("Samsung", "Samsung Electronics"). This allows Home Assistant's SSDP component to find compatible TVs.
    *   `dhcp`: It includes a list of known Samsung MAC address prefixes (`4844F7*`, `606BBD*`, etc.) and a hostname pattern (`tizen*`). This allows Home Assistant's DHCP discovery to identify potential Samsung TVs based on network leases.
    *   `zeroconf`: It lists an AirPlay service type (`_airplay._tcp.local.`) and filters by manufacturer property (`samsung*`). This allows Home Assistant's Zeroconf (mDNS) component to find compatible TVs broadcasting this service, often used by newer Samsung TVs.

2.  **`config_flow.py`**: The config flow handler implements dedicated steps to process the discovery information received from the configured discovery methods:
    *   `async_step_ssdp`: This method is triggered when an SSDP device matching the criteria in `manifest.json` is found. It extracts information like the host, UDN, manufacturer, and model from the `SsdpServiceInfo` object (`discovery_info.upnp`, `discovery_info.ssdp_location`). It then attempts to get further device info using the `SamsungTVBridge` (`await self._async_get_and_check_device_info`) and sets the unique ID based on the UDN (`await self._async_set_unique_id_from_udn`), ultimately leading to the `async_step_confirm` flow.
    *   `async_step_dhcp`: This method is triggered by DHCP discovery. It extracts the MAC address and IP address from the `DhcpServiceInfo`. It then proceeds to set the unique ID (`await self._async_set_device_unique_id`) and goes to `async_step_confirm`.
    *   `async_step_zeroconf`: This method is triggered by Zeroconf (mDNS) discovery. It extracts the device ID (used as MAC) and host from the `ZeroconfServiceInfo`. Similar to the DHCP flow, it sets the unique ID and proceeds to `async_step_confirm`.

The integration correctly uses the `config_flow` to handle discovered devices via specific `async_step_*` methods corresponding to the discovery protocols declared in the `manifest.json`. This allows Home Assistant to automatically detect compatible Samsung TVs and prompt the user to configure them, significantly improving the user experience.

## Suggestions

No suggestions needed. The integration fully complies with the discovery rule.
```

_Created at 2025-05-25 11:31:10. Prompt tokens: 30713, Output tokens: 827, Total tokens: 32400_
