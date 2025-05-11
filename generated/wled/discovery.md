# wled: discovery

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [discovery](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery)                                                     |
| Status | **done**                                                                 |

## Overview

The `discovery` rule requires integrations to support automatic discovery of devices where applicable, making setup easier for users. WLED devices are network-based and announce themselves on the local network using mDNS (Zeroconf). Therefore, this rule applies to the `wled` integration.

The `wled` integration correctly implements discovery via mDNS (Zeroconf). This is evident from the following:

1.  **`manifest.json`**:
    The manifest file includes the `zeroconf` key, specifying the service type that Home Assistant should listen for:
    ```json
    {
      "domain": "wled",
      "name": "WLED",
      "zeroconf": ["_wled._tcp.local."]
    }
    ```
    This tells Home Assistant to trigger the WLED config flow when a `_wled._tcp.local.` service is discovered on the network.

2.  **`config_flow.py`**:
    The `WLEDFlowHandler` class in `config_flow.py` implements the necessary steps to handle Zeroconf discovery:
    *   `async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo)`: This method is called when a WLED device is discovered.
        *   It extracts the host from `discovery_info.host`.
        *   It attempts to retrieve the MAC address from `discovery_info.properties` for an early unique ID check.
        *   It calls `_async_get_device(discovery_info.host)` to connect to the WLED device and fetch its information, which includes the MAC address.
        *   It uses `await self.async_set_unique_id(self.discovered_device.info.mac_address)` to set a unique ID for the device, ensuring it's only configured once.
        *   It uses `self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.host})` to prevent duplicate entries and to allow updating the host IP address if it has changed for an already configured device.
        *   It prepares context for the confirmation step, including the device name.
    *   `async_step_zeroconf_confirm(self, user_input: dict[str, Any] | None = None)`: This method presents a confirmation dialog to the user, allowing them to add the discovered WLED device.
        ```python
        async def async_step_zeroconf(
            self, discovery_info: ZeroconfServiceInfo
        ) -> ConfigFlowResult:
            """Handle zeroconf discovery."""
            # Abort quick if the mac address is provided by discovery info
            if mac := discovery_info.properties.get(CONF_MAC):
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: discovery_info.host}
                )

            self.discovered_host = discovery_info.host
            try:
                self.discovered_device = await self._async_get_device(discovery_info.host)
            except WLEDConnectionError:
                return self.async_abort(reason="cannot_connect")

            await self.async_set_unique_id(self.discovered_device.info.mac_address)
            self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.host})

            self.context.update(
                {
                    "title_placeholders": {"name": self.discovered_device.info.name},
                    "configuration_url": f"http://{discovery_info.host}",
                }
            )
            return await self.async_step_zeroconf_confirm()
        ```

This implementation aligns with the requirements of the `discovery` rule, providing a seamless experience for users to add their WLED devices to Home Assistant.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:58:39. Prompt tokens: 23725, Output tokens: 980, Total tokens: 26318_
