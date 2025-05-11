# wled: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `discovery-update-info` rule requires integrations that use discovery to update the network information (e.g., IP address) of a device if it changes, provided the integration can confirm it's the same device using a unique identifier.

The `wled` integration uses Zeroconf for discovering devices, as declared in its `manifest.json`:
```json
{
  "domain": "wled",
  "name": "WLED",
  // ...
  "zeroconf": ["_wled._tcp.local."]
}
```
This makes the rule applicable to the `wled` integration.

The integration's `config_flow.py` handles Zeroconf discovery in the `async_step_zeroconf` method. This method correctly implements the requirements of the rule:

1.  **Unique ID Setting**: It sets a unique ID for the discovered device based on its MAC address.
    *   First, it attempts to get the MAC address from the `discovery_info.properties`:
        ```python
        # config_flow.py
        if mac := discovery_info.properties.get(CONF_MAC):
            await self.async_set_unique_id(mac)
            # ...
        ```
    *   If the MAC address is not in the properties, it fetches device information (which includes the MAC address) by connecting to the device:
        ```python
        # config_flow.py
        self.discovered_device = await self._async_get_device(discovery_info.host)
        await self.async_set_unique_id(self.discovered_device.info.mac_address)
        ```

2.  **Updating Host Information**: After setting the unique ID, it calls `self._abort_if_unique_id_configured` with the `updates` parameter. This parameter includes the new host (IP address) discovered. If a config entry with the same unique ID already exists, Home Assistant will update its configuration (specifically the `CONF_HOST`) with the new host information and abort the current discovery flow.
    ```python
    # config_flow.py
    # Case 1: MAC from properties
    self._abort_if_unique_id_configured(
        updates={CONF_HOST: discovery_info.host}
    )

    # Case 2: MAC fetched from device
    self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.host})
    ```

This implementation ensures that if a WLED device's IP address changes, and it is rediscovered via Zeroconf, its existing configuration entry in Home Assistant will be updated with the new IP address, allowing the integration to continue communicating with the device without requiring manual reconfiguration by the user.

Thus, the `wled` integration fully follows the `discovery-update-info` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:59:03. Prompt tokens: 22062, Output tokens: 754, Total tokens: 24283_
