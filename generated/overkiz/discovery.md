# overkiz: discovery

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [discovery](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery)                                                     |
| Status | **todo**                                                                 |

## Overview

The `discovery` rule applies to the `overkiz` integration because Overkiz hubs (like Somfy TaHoma) are network-attached devices that can be discovered via DHCP and Zeroconf (mDNS). Implementing discovery improves the user experience by simplifying the setup process.

The `overkiz` integration currently partially follows this rule:

1.  **Declaration of Discovery Methods:**
    The `manifest.json` correctly declares support for DHCP and Zeroconf discovery:
    ```json
    // homeassistant/components/overkiz/manifest.json
    {
      "domain": "overkiz",
      // ...
      "dhcp": [
        {
          "hostname": "gateway*",
          "macaddress": "F8811A*"
        }
      ],
      // ...
      "zeroconf": [
        {
          "type": "_kizbox._tcp.local.",
          "name": "gateway*"
        },
        {
          "type": "_kizboxdev._tcp.local.",
          "name": "gateway*"
        }
      ]
    }
    ```

2.  **Implementation of Discovery Steps:**
    The `config_flow.py` implements the necessary `async_step_dhcp` and `async_step_zeroconf` methods:
    *   `async_step_dhcp(self, discovery_info: DhcpServiceInfo)`: Handles DHCP discovery, extracts the gateway ID, sets `self._host`, and proceeds to `self._process_discovery`.
    *   `async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo)`: Handles Zeroconf discovery, extracts gateway ID and properties, sets `self._host` (and `self._api_type` for developer mode discovery), and proceeds to `self._process_discovery`.

3.  **Initiation of Config Flow:**
    The `_process_discovery(self, gateway_id: str)` method correctly sets the unique ID for the config entry and then calls `await self.async_step_user()` to start the user-guided configuration process. This allows users to set up newly discovered devices.

However, the integration does not fully follow the rule's best practices regarding updates for *existing* configurations. The rule states: "Using a network-based setup, also allows the configuration of the integration to be updated once the device receives a new IP address." The example provided in the rule documentation demonstrates using the `updates` parameter of `self._abort_if_unique_id_configured()` to achieve this.

In `homeassistant/components/overkiz/config_flow.py`, the `_process_discovery` method calls `self._abort_if_unique_id_configured()` without any `updates`:
```python
// homeassistant/components/overkiz/config_flow.py
async def _process_discovery(self, gateway_id: str) -> ConfigFlowResult:
    """Handle discovery of a gateway."""
    await self.async_set_unique_id(gateway_id)
    self._abort_if_unique_id_configured() // Issue: No 'updates' parameter passed
    self.context["title_placeholders"] = {"gateway_id": gateway_id}

    return await self.async_step_user()
```
Because the `updates` parameter is not used, if an already configured Overkiz hub (especially one using the local API where `CONF_HOST` is critical) gets a new IP address and is rediscovered, its `CONF_HOST` in the Home Assistant configuration entry will not be automatically updated. The user might then encounter connection issues until they manually reconfigure or re-authenticate the integration.

## Suggestions

To fully comply with the rule and improve robustness for local API connections when IP addresses change, the `_process_discovery` method should be modified to pass the newly discovered host to `_abort_if_unique_id_configured`. This update is primarily relevant for entries configured to use the local API.

1.  **Modify `_process_discovery` in `config_flow.py`:**

    The `self._host` variable is set by `async_step_dhcp` and `async_step_zeroconf` before `_process_discovery` is called. This host should be used to update an existing config entry if it's configured for local API.

    ```python
    # homeassistant/components/overkiz/config_flow.py

    # ... (other imports)
    from homeassistant.const import CONF_HOST # Ensure CONF_HOST is imported
    from .const import CONF_API_TYPE # Ensure CONF_API_TYPE is imported
    from pyoverkiz.enums import APIType # Ensure APIType is imported

    # ...

    class OverkizConfigFlow(ConfigFlow, domain=DOMAIN):
        # ... (existing code)

        async def _process_discovery(self, gateway_id: str) -> ConfigFlowResult:
            """Handle discovery of a gateway."""
            await self.async_set_unique_id(gateway_id)

            updates_payload = {}
            # Check if there's an existing entry for this unique_id
            current_entry = self._async_current_entry()
            if (
                current_entry
                and current_entry.data.get(CONF_API_TYPE) == APIType.LOCAL
                and self._host  # self._host is set by async_step_dhcp/zeroconf
            ):
                # Only update CONF_HOST if the existing entry is for local API
                # and the newly discovered host is different from the stored one.
                if current_entry.data.get(CONF_HOST) != self._host:
                    updates_payload[CONF_HOST] = self._host
                    # Potentially, self._api_type could also be updated if Zeroconf discovery
                    # (_kizboxdev._tcp.local.) implies APIType.LOCAL and the existing entry
                    # was somehow misconfigured or needs this flag reinforced.
                    # For _kizboxdev, self._api_type is set to APIType.LOCAL in async_step_zeroconf.
                    # if self._api_type == APIType.LOCAL and \
                    #    current_entry.data.get(CONF_API_TYPE) != APIType.LOCAL:
                    #    updates_payload[CONF_API_TYPE] = self._api_type

            self._abort_if_unique_id_configured(
                updates=updates_payload if updates_payload else None
            )

            self.context["title_placeholders"] = {"gateway_id": gateway_id}
            return await self.async_step_user()

        # ... (rest of the class)
    ```

2.  **Why this change helps:**
    *   By passing `updates={CONF_HOST: self._host}` (when applicable for local API entries), the `_abort_if_unique_id_configured` method in Home Assistant's core will automatically update the `CONF_HOST` in the `ConfigEntry`'s data if the device is already configured.
    *   This ensures that if a device's IP address changes and it's rediscovered, Home Assistant can seamlessly update its connection information for local API connections, preventing connection failures and improving user experience.
    *   The check `current_entry.data.get(CONF_HOST) != self._host` ensures that an update and reload only happen if the host has actually changed, avoiding unnecessary reloads.

_Created at 2025-05-28 12:28:38. Prompt tokens: 87579, Output tokens: 1786, Total tokens: 94667_
