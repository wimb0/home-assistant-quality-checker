```markdown
# fritzbox: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info) |
| Status | **done**                                                                 |

## Overview

The rule `discovery-update-info` requires integrations that are discoverable to use discovery information to update the network information (like IP address or hostname) of existing config entries if the device's address changes, provided the integration can confidently identify the device using a unique ID.

This rule applies to the `fritzbox` integration because it implements SSDP discovery (`manifest.json` includes `"ssdp": [...]`).

The analysis of the provided code shows that the `fritzbox` integration correctly follows this rule. The `config_flow.py` includes an `async_step_ssdp` method which handles discovery flows initiated via SSDP.

Within `async_step_ssdp`, the flow performs the following key steps to comply with the rule:

1.  It extracts the hostname (`host`) from the SSDP discovery information (`discovery_info.ssdp_location`).
2.  It extracts the Unique Device Name (UDN) from the SSDP information (`discovery_info.upnp.get(ATTR_UPNP_UDN)`).
3.  It sets the flow's unique ID using the extracted UDN (`await self.async_set_unique_id(uuid)`). The UDN serves as a stable identifier for the Fritzbox device.
4.  It then calls `self._abort_if_unique_id_configured({CONF_HOST: host})`. This is the standard method in Home Assistant config flows to check if an entry with the same unique ID already exists and, if so, abort the current discovery flow while simultaneously updating the specified configuration values (in this case, `CONF_HOST`) on the existing entry.

This pattern ensures that if a Fritzbox's IP address changes but its UDN remains the same (which is typical for SSDP devices), a new discovery event will trigger the `async_step_ssdp` flow, which will then update the `host` stored in the existing config entry using `_abort_if_unique_id_configured`, without requiring the user to manually reconfigure the integration.

## Suggestions

No suggestions needed. The integration correctly implements the rule.
```

_Created at 2025-05-25 11:35:42. Prompt tokens: 19171, Output tokens: 568, Total tokens: 20453_
