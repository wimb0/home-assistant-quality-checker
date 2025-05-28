# overkiz: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `discovery-update-info` rule applies to the `overkiz` integration because it utilizes both DHCP and Zeroconf discovery mechanisms, as indicated in its `manifest.json` file.

The integration currently does NOT fully follow this rule. While it uses discovery to identify new and existing devices via a unique gateway ID, it does not update the network information (such as `CONF_HOST`, `CONF_API_TYPE`, or `CONF_VERIFY_SSL`) of an already configured device if these details change (e.g., due to a new IP address or enabling developer mode).

Specifically, in `homeassistant/components/overkiz/config_flow.py`:
- The discovery methods `async_step_dhcp` and `async_step_zeroconf` correctly determine the `gateway_id` and populate class members like `self._host`, `self._api_type`, and `self._verify_ssl` with the latest discovered network parameters.
- These methods then call `_process_discovery(self, gateway_id: str)`.
- Inside `_process_discovery`, `await self.async_set_unique_id(gateway_id)` is called, followed by `self._abort_if_unique_id_configured()`.
- The call to `self._abort_if_unique_id_configured()` is made without the `updates` parameter. According to the rule, if a device with the same unique ID is found, its network information should be updated using this `updates` parameter. For example, `self._abort_if_unique_id_configured(updates={CONF_HOST: new_host_value, CONF_API_TYPE: new_api_type})`.

As a result, if a previously configured Overkiz hub gets a new IP address or if its API access method changes (e.g., developer mode enabled providing a local API endpoint), the existing configuration entry in Home Assistant is not updated with this new information.

## Suggestions

To make the `overkiz` integration compliant with the `discovery-update-info` rule, the `_process_discovery` method in `homeassistant/components/overkiz/config_flow.py` should be modified to pass the discovered network information to `self._abort_if_unique_id_configured()`.

The class members `self._host`, `self._api_type`, and `self._verify_ssl` are populated by the respective discovery steps (`async_step_dhcp` or `async_step_zeroconf`) before `_process_discovery` is called. These values represent the most current information obtained from the network for the discovered gateway.

Modify `_process_discovery` as follows:

```python
# homeassistant/components/overkiz/config_flow.py

# ... import APIType, CONF_API_TYPE, CONF_VERIFY_SSL if not already imported at the top
# from pyoverkiz.enums import APIType
# from .const import CONF_API_TYPE (already in const.py, might need to import from .const)
# CONF_HOST, CONF_VERIFY_SSL are already in homeassistant.const

# ... inside OverkizConfigFlow class

    async def _process_discovery(self, gateway_id: str) -> ConfigFlowResult:
        """Handle discovery of a gateway."""
        await self.async_set_unique_id(gateway_id)

        # Prepare the updates dictionary with information gathered during discovery
        # self._host, self._api_type, and self._verify_ssl are class members
        # populated by the calling discovery step (async_step_dhcp or async_step_zeroconf).
        updates_payload: dict[str, Any] = {}

        # self._host should always be set by the discovery methods.
        updates_payload[CONF_HOST] = self._host
        
        # self._api_type reflects the API type implied or defaulted by this specific discovery.
        # self._verify_ssl reflects the SSL setting implied or defaulted for this discovery.
        updates_payload[CONF_API_TYPE] = self._api_type 
        updates_payload[CONF_VERIFY_SSL] = self._verify_ssl

        # Abort if already configured, and update the entry with new network info if changed.
        self._abort_if_unique_id_configured(updates=updates_payload)
        
        self.context["title_placeholders"] = {"gateway_id": gateway_id}
        return await self.async_step_user()
```

**Reasoning for the change:**

*   This modification ensures that when a device with a known `gateway_id` is rediscovered, the `_abort_if_unique_id_configured` method will receive the latest `CONF_HOST`, `CONF_API_TYPE`, and `CONF_VERIFY_SSL` values derived from the discovery.
*   If these values differ from those in the existing configuration entry, `_abort_if_unique_id_configured` will update the entry's data and trigger a reload of the integration with the new parameters.
*   This correctly handles scenarios such as:
    *   A local API-configured hub obtaining a new IP address.
    *   A hub, initially configured for cloud API, having developer mode enabled and being rediscovered via its local API endpoint (`_kizboxdev._tcp.local.`). In this case, `CONF_HOST`, `CONF_API_TYPE` (to `LOCAL`), and `CONF_VERIFY_SSL` would be updated. The subsequent reload would likely lead to an authentication failure (as cloud credentials won't work for local API token auth), triggering a re-auth flow where the user can provide the local API token.

This change aligns the integration with the rule's requirement to keep network information up-to-date via discovery, improving reliability in dynamic network environments.

_Created at 2025-05-28 12:30:32. Prompt tokens: 87180, Output tokens: 1414, Total tokens: 98006_
