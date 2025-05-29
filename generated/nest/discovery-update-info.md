# nest: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info)                                                     |
| Status | **exempt**                                       |
| Reason | The integration is primarily cloud-based. Home Assistant communicates with Nest devices via the Google SDM API, not directly using local IP addresses. Therefore, the integration does not store or rely on local device IP addresses in its configuration in a way that would require updates from DHCP discovery. |

## Overview

The `discovery-update-info` rule mandates that integrations use discovery information (like mDNS or DHCP) to update the network information (e.g., IP address) of a device if it changes after initial setup. This is to ensure continued connectivity for devices with dynamic IP addresses.

The Nest integration is **exempt** from this rule. Here's why:

1.  **Cloud-Based Architecture:** The Nest integration is `iot_class: "cloud_push"` as specified in its `manifest.json`. Home Assistant interacts with Nest devices (thermostats, cameras, sensors) through the Google Smart Device Management (SDM) cloud API. It does not establish direct local connections to devices using their IP addresses for core functionality.

2.  **No Local IP Storage in Config Entry:** The configuration entry for the Nest integration is centered around a `project_id` (Device Access Project ID) and authentication tokens. It does not store `CONF_HOST` or individual device IP addresses that would need to be updated. This can be seen in `config_flow.py` where the unique ID for the config entry is set using `await self.async_set_unique_id(project_id)`.

3.  **Camera Streams via Cloud API:**
    *   For RTSP cameras (`NestRTSPEntity` in `camera.py`), the stream URL is obtained by calling `_rtsp_live_stream_trait.generate_rtsp_stream()`, which is an SDM API call. If a device's network details change, the SDM API is expected to provide the updated stream information. The integration includes a `StreamRefresh` mechanism to handle expiring stream tokens and implicitly fetch new stream details if necessary.
    *   For WebRTC cameras (`NestWebRTCEntity` in `camera.py`), sessions are also established via the SDM API (`trait.generate_web_rtc_stream(offer_sdp)`).
    Local IP changes are handled at the cloud level, not by HA updating a stored IP.

4.  **DHCP Discovery for Initial Setup:** The `manifest.json` includes `dhcp` entries:
    ```json
    "dhcp": [
      { "macaddress": "18B430*" },
      { "macaddress": "641666*" },
      { "macaddress": "D8EB46*" }
    ]
    ```
    This allows Home Assistant to detect Nest devices on the network and suggest setting up the integration. However, this is for initial discovery. The rule's info box states: "If you are using DHCP discovery, and you want to receive discovery flows for updated IP addresses, be sure to register the MAC address in the device info and set `registered_devices` to `true` in the manifest." The Nest `manifest.json` does *not* include `registered_devices: true`. This means it does not opt-in to receiving discovery flows for IP address updates of already configured devices.

5.  **No `async_step_dhcp` for Updates:** The `config_flow.py` does not implement an `async_step_dhcp` method. Even if it did, the Nest config entry is per `project_id`, not per physical device MAC address. Updating a specific device's IP within a project-level config entry is not how this integration is structured.

Because the integration's functionality does not depend on Home Assistant knowing or storing the local IP addresses of Nest devices, the requirement to update this information based on discovery is not applicable. The core problem the rule solves (maintaining connectivity to local devices with dynamic IPs) is sidestepped by Nest's cloud-centric communication model.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:05:42. Prompt tokens: 32540, Output tokens: 972, Total tokens: 39408_
