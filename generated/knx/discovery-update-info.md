# knx: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [knx](https://www.home-assistant.io/integrations/knx/) |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `discovery-update-info` rule applies to the `knx` integration. This rule requires integrations that discover network devices or services to use discovery information to update network details (like IP addresses) if they change after initial setup. This is to handle dynamic IP addresses common in user networks.

The `knx` integration supports discovering KNX/IP gateways, particularly for "Automatic" and "Tunneling" connection types, using the `GatewayScanner` from the `xknx` library (as seen in `homeassistant/components/knx/config_flow.py`). When a tunneling connection is configured, the IP address (`CONF_HOST`) and port of the gateway are stored in the `ConfigEntry`.

Currently, the `knx` integration does **not** follow this rule. While it discovers gateways during initial setup or manual reconfiguration via the options flow, it does not automatically update the stored IP address of a configured gateway if that gateway's IP changes. If a gateway's IP address changes, the connection will likely fail, and the user must manually reconfigure the integration through the options flow to point to the new IP address.

There is no mechanism in place that:
1.  Persistently monitors or re-scans for the configured gateway in the background.
2.  Identifies a previously configured gateway by a stable unique identifier (like its Individual Address or MAC address).
3.  Automatically updates the `CONF_HOST` in the `ConfigEntry` if this gateway is re-discovered at a new IP address.
4.  Re-initializes the connection with the updated IP address.

The pattern shown in the rule's example, often involving `_abort_if_unique_id_configured(updates={CONF_HOST: host})` within a discovery-triggered config flow step (like `async_step_zeroconf`), is not present for updating KNX gateway IP addresses post-setup. The `knx` integration's `manifest.json` does not declare standard Home Assistant discovery methods like `zeroconf` or `dhcp`, relying on its custom `GatewayScanner`.

## Suggestions

To make the `knx` integration compliant with the `discovery-update-info` rule, the following changes could be implemented, primarily for tunneling connection types where a specific host IP is stored:

1.  **Store a Stable Unique Identifier for the Gateway:**
    *   When a tunneling connection is successfully established (e.g., in `KNXModule.connection_state_changed_cb` or after `KNXInterfaceDevice.update`), retrieve a stable unique identifier for the connected gateway. The gateway's Individual Address (IA) is a good candidate, available from `GatewayDescriptor.individual_address` or `xknx.knxip_interface.gateway.individual_address`.
    *   Store this identifier (e.g., `configured_gateway_ia`) in the `ConfigEntry.data` or `ConfigEntry.options`.

2.  **Implement Re-discovery on Connection Failure:**
    *   When the KNX connection is lost (e.g., detected in `KNXModule.connection_state_changed_cb` when transitioning to a disconnected state after being connected), or periodically if deemed appropriate, trigger a re-scan for KNX gateways using `GatewayScanner`.

3.  **Match and Update Logic:**
    *   In the callback handling the results of the `GatewayScanner`:
        *   Iterate through the discovered gateways (`found_gateways`).
        *   For each discovered gateway, compare its `individual_address` with the stored `configured_gateway_ia`.
        *   If a match is found AND the discovered `gateway.ip_addr` is different from the currently stored `CONF_HOST` in the `ConfigEntry.data`:
            *   Log that the gateway has been found at a new IP address.
            *   Create a new data dictionary for the `ConfigEntry` with the updated `CONF_HOST`:
                ```python
                # Example within a relevant class method
                # entry = self.knx_module.entry (assuming knx_module has access to the entry)
                # new_ip = discovered_gateway.ip_addr
                # current_port = entry.data.get(CONF_PORT)
                #
                # new_data = entry.data.copy()
                # new_data[CONF_HOST] = new_ip
                # self.hass.config_entries.async_update_entry(entry, data=new_data)
                ```
            *   After updating the `ConfigEntry`, the integration should re-initialize its connection. This might involve calling `async_reload` on the config entry or having the `xknx` library reconfigure its connection parameters and attempt to reconnect.

**Example Snippet (Conceptual):**

This is a conceptual example of where such logic might be initiated or reside. The actual implementation would need careful integration into the existing `KNXModule` and connection management.

```python
# Potentially in homeassistant/components/knx/__init__.py within KNXModule

from xknx.io import GatewayScanner
from xknx.core import XknxConnectionState
# ... other imports

class KNXModule:
    # ... existing methods ...

    async def _handle_disconnected_state(self):
        """Attempt to find the configured gateway if its IP changed."""
        if self.entry.data.get(CONF_KNX_CONNECTION_TYPE) not in [
            CONF_KNX_TUNNELING,
            CONF_KNX_TUNNELING_TCP,
            CONF_KNX_TUNNELING_TCP_SECURE,
        ]:
            return # Only applicable for tunneling where a host is fixed

        configured_gateway_ia_str = self.entry.data.get("configured_gateway_ia") # Needs to be stored first
        current_host = self.entry.data.get(CONF_HOST)

        if not configured_gateway_ia_str or not current_host:
            _LOGGER.debug("Missing configured gateway IA or host for IP update check.")
            return

        _LOGGER.info("KNX connection lost. Scanning for gateway %s.", configured_gateway_ia_str)
        scanner = GatewayScanner(self.xknx) # self.xknx might need to be passed or re-created carefully
        # Consider running scanner.async_scan() in an executor if it's blocking
        found_gateways = await self.hass.async_add_executor_job(scanner.scan)

        for gateway_descriptor in found_gateways:
            if gateway_descriptor.individual_address and \
               str(gateway_descriptor.individual_address) == configured_gateway_ia_str and \
               gateway_descriptor.ip_addr != current_host:

                _LOGGER.info(
                    "Found configured KNX gateway %s at new IP %s (was %s). Updating configuration.",
                    configured_gateway_ia_str,
                    gateway_descriptor.ip_addr,
                    current_host,
                )
                new_data = self.entry.data.copy()
                new_data[CONF_HOST] = gateway_descriptor.ip_addr
                # Potentially update port if it can change and is discovered
                # new_data[CONF_PORT] = gateway_descriptor.port

                # Ensure other relevant data for the connection type is preserved
                if self.hass.config_entries.async_update_entry(self.entry, data=new_data):
                    _LOGGER.info("KNX gateway IP updated. Attempting to reload integration.")
                    # Reloading the entry will re-trigger setup with the new IP
                    await self.hass.config_entries.async_reload(self.entry.entry_id)
                return # Found and updated

        _LOGGER.info("Configured KNX gateway %s not found at a new IP.", configured_gateway_ia_str)


    def connection_state_changed_cb(self, state: XknxConnectionState) -> None:
        """Call invoked after a KNX connection state change was received."""
        self.connected = state == XknxConnectionState.CONNECTED
        if not self.connected and self.entry.data.get("configured_gateway_ia"): # Check if we were previously connected and have an IA
            # Schedule the re-discovery task
            self.hass.async_create_task(self._handle_disconnected_state())

        for device in self.xknx.devices:
            device.after_update()

    # In async_setup_entry or after successful connection:
    # async def store_gateway_ia_if_needed(self):
    #     if self.entry.data.get(CONF_KNX_CONNECTION_TYPE) in [...] and \
    #        not self.entry.data.get("configured_gateway_ia") and \
    #        self.xknx.knxip_interface and self.xknx.knxip_interface.gateway:
    #         gateway_ia = str(self.xknx.knxip_interface.gateway.individual_address)
    #         if gateway_ia != "0.0.0": # Ensure valid IA
    #             new_data = self.entry.data.copy()
    #             new_data["configured_gateway_ia"] = gateway_ia
    #             self.hass.config_entries.async_update_entry(self.entry, data=new_data)
    #             _LOGGER.info("Stored IA %s for configured KNX gateway.", gateway_ia)
```

4.  **Testing:** Ensure this mechanism correctly updates the IP and handles cases where the gateway is not found or other errors occur.

By implementing such a mechanism, the `knx` integration would become more resilient to IP address changes for configured gateways, aligning with the `discovery-update-info` rule. This would particularly improve the user experience for tunneling connections.

_Created at 2025-05-14 13:36:25. Prompt tokens: 101182, Output tokens: 2320, Total tokens: 107123_
