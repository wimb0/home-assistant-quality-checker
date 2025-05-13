# music_assistant: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `discovery-update-info` rule requires that integrations using discovery mechanisms (like mDNS/Zeroconf or DHCP) update the network information (e.g., IP address) of already configured devices if they are re-discovered with new network details. This ensures Home Assistant can continue to communicate with devices even if their IP addresses change, provided a stable unique identifier confirms it's the same device.

This rule applies to the `music_assistant` integration.
The `manifest.json` file specifies Zeroconf discovery:
```json
{
  "domain": "music_assistant",
  ...
  "zeroconf": ["_mass._tcp.local."]
}
```
This means the integration will be notified of Music Assistant servers discovered on the network via mDNS.

The integration correctly follows this rule. In its `config_flow.py`, the `async_step_zeroconf` method handles discovered services:

```python
# homeassistant/components/music_assistant/config_flow.py
async def async_step_zeroconf(
    self, discovery_info: ZeroconfServiceInfo
) -> ConfigFlowResult:
    """Handle a discovered Mass server.

    This flow is triggered by the Zeroconf component. It will check if the
    host is already configured and delegate to the import step if not.
    """
    # abort if discovery info is not what we expect
    if "server_id" not in discovery_info.properties:
        return self.async_abort(reason="missing_server_id")
    # abort if we already have exactly this server_id
    # reload the integration if the host got updated
    self.server_info = ServerInfoMessage.from_dict(discovery_info.properties)
    await self.async_set_unique_id(self.server_info.server_id)
    self._abort_if_unique_id_configured(
        updates={CONF_URL: self.server_info.base_url},
        reload_on_update=True,
    )
    try:
        await get_server_info(self.hass, self.server_info.base_url)
    except CannotConnect:
        return self.async_abort(reason="cannot_connect")
    return await self.async_step_discovery_confirm()
```

Key aspects demonstrating compliance:
1.  **Unique ID:** `await self.async_set_unique_id(self.server_info.server_id)` is called. The `server_id` is extracted from the `discovery_info.properties`. This `server_id` acts as the stable unique identifier for the Music Assistant server.
2.  **Update Mechanism:** `self._abort_if_unique_id_configured(updates={CONF_URL: self.server_info.base_url}, reload_on_update=True,)` is used.
    *   If a config entry with the same unique ID (`server_id`) already exists, this function will update its configuration.
    *   The `updates` dictionary specifies that the `CONF_URL` (which stores the Music Assistant server's URL, including its IP address or hostname) should be updated with `self.server_info.base_url`. The `base_url` is derived from the current discovery information, reflecting any potential changes in IP address.
    *   `reload_on_update=True` ensures that the integration is reloaded after the configuration update, applying the new URL immediately.

This implementation matches the example and intent of the rule, allowing the integration to adapt to changes in the Music Assistant server's network address.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:17:00. Prompt tokens: 30295, Output tokens: 931, Total tokens: 32801_
