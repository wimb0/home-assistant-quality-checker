```markdown
# fritzbox: discovery

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [discovery](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery) |
| Status | **done**                                                                 |

## Overview

The `discovery` rule requires integrations for discoverable network devices to implement one or more discovery methods to simplify setup for users and handle potential IP address changes.

The AVM FRITZ!Box devices are network devices known to support discovery protocols like SSDP. The `fritzbox` integration correctly identifies this and implements discovery using SSDP.

The `manifest.json` file explicitly lists SSDP as a discovery method:
```json
  "ssdp": [
    {
      "st": "urn:schemas-upnp-org:device:fritzbox:1"
    }
  ]
```
This tells Home Assistant's discovery component to look for devices announcing this specific service type (`st`) via SSDP and trigger the `fritzbox` config flow.

The `config_flow.py` file contains the necessary `async_step_ssdp` method to handle the discovery information received:
```python
    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a flow initialized by discovery."""
        host = urlparse(discovery_info.ssdp_location).hostname
        assert isinstance(host, str)

        # ... (IPv6 link local check and unique ID handling) ...

        if uuid := discovery_info.upnp.get(ATTR_UPNP_UDN):
            uuid = uuid.removeprefix("uuid:")
            await self.async_set_unique_id(uuid)
            self._abort_if_unique_id_configured({CONF_HOST: host})

        # ... (checking for existing flows/entries) ...

        self._host = host
        # ... (setting name and context) ...
        return await self.async_step_confirm()
```
This code correctly extracts the host from the discovery information, attempts to set a unique ID based on the UPnP UDN, checks if the device is already configured or a flow is in progress, and proceeds to a confirmation step (`async_step_confirm`).

The integration thus successfully implements discovery for devices that announce their presence via SSDP, fulfilling the requirements of the `discovery` rule.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:35:35. Prompt tokens: 19570, Output tokens: 589, Total tokens: 20879_
