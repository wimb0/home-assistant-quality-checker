```markdown
# samsungtv: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info)                                                     |
| Status | **done**                                                                 |

## Overview

This rule requires that integrations leveraging network discovery protocols should use the information from subsequent discoveries to update the network details (like IP address) stored in the config entry for already configured devices. This is essential for handling dynamic IP addresses in user networks. The Samsung TV integration utilizes SSDP, DHCP, and Zeroconf discovery, making this rule applicable.

The analysis of the provided code shows that the `samsungtv` integration fully implements the requirements of the `discovery-update-info` rule.

Here's a breakdown of how the integration complies:

1.  **Discovery Protocols:** The `manifest.json` file explicitly lists `ssdp`, `dhcp`, and `zeroconf` as discovery dependencies. This confirms the integration uses network discovery.
2.  **DHCP `registered_devices`:** The `manifest.json` includes `dhcp` discovery with `"registered_devices": true`. This is a key part of handling dynamic IPs via DHCP, as it tells Home Assistant to create a discovery flow for devices with a known MAC address seen on the network, even if they have a new IP.
3.  **Stable Identifier (`unique_id`):** The config flow (`config_flow.py`) uses a stable identifier, `_udn`, derived from the UDN found via SSDP or the device's REST API, and falls back to the MAC address (`_mac`) if UDN is not available, for setting the config entry's `unique_id`.
4.  **Updating Config Entry on Discovery:** The config flow logic in `async_step_ssdp`, `async_step_dhcp`, and `async_step_zeroconf` calls the internal method `_async_update_existing_matching_entry`. This method actively searches for existing config entries that match the discovered device based on its MAC address (`CONF_MAC`) or UDN (`unique_id`).
5.  **Host and Network Info Updates:** If `_async_update_existing_matching_entry` finds a matching configured entry, it updates the entry's data (`entry.data`) with the newly discovered `CONF_HOST`, `CONF_MAC`, `CONF_MODEL`, `CONF_SSDP_RENDERING_CONTROL_LOCATION`, and `CONF_SSDP_MAIN_TV_AGENT_LOCATION` if the new information is available and different from what is currently stored. This update is performed via `hass.config_entries.async_update_entry`.
6.  **Reload on Update:** After updating an existing entry, `_async_update_existing_matching_entry` triggers a reload of the config entry (`self.hass.async_create_task(self.hass.config_entries.async_reload(entry.entry_id))`) if the entry is not already loaded. This ensures the integration instance picks up the new network information.
7.  **`_abort_if_unique_id_configured` with updates:** The discovery steps also call `self._abort_if_unique_id_configured(updates=updates, reload_on_update=False)`. Although the primary update logic is in `_async_update_existing_matching_entry`, this secondary call reinforces the pattern and ensures that the configuration flow aborts correctly while providing potential updates.

The combination of configured discovery protocols, the use of stable identifiers for the unique ID, the explicit logic to find and update matching config entries with current network information, and the subsequent reloading of the entry demonstrates adherence to the rule's requirements.

## Suggestions

No suggestions needed. The integration correctly handles discovery updates for configured devices.
```

_Created at 2025-05-25 11:31:23. Prompt tokens: 30314, Output tokens: 882, Total tokens: 32658_
