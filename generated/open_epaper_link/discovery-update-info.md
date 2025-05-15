# open_epaper_link: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not discover the OpenEPaperLink Access Point (AP) via network discovery methods like mDNS, SSDP, or DHCP. The AP's IP address is manually configured by the user. Therefore, the rule's requirement to update network information based on discovery data does not apply, as per the rule's exception: "Integrations where the devices can't be discovered are exempt from this rule." |

## Overview

The `discovery-update-info` rule requires integrations that discover devices or services on the network to use subsequent discovery information to update network details (like IP addresses) if they change. This helps maintain connectivity if a device's IP address is dynamic.

The `open_epaper_link` integration communicates with an OpenEPaperLink Access Point (AP), which acts as a hub for e-paper tags. The critical aspect for this rule is how the Home Assistant integration finds and connects to this AP.

1.  **Manifest Analysis (`manifest.json`):**
    The `manifest.json` for `open_epaper_link` does not declare any discovery mechanisms such as `zeroconf`, `ssdp`, or `dhcp`. This indicates that the integration does not use Home Assistant's built-in discovery helpers to find the AP on the network.

2.  **Config Flow Analysis (`config_flow.py`):**
    *   The primary configuration step is `async_step_user`. This step presents a form (`STEP_USER_DATA_SCHEMA`) that requires the user to manually input the `CONF_HOST` (IP address or hostname) of the OpenEPaperLink AP.
        ```python
        # config_flow.py
        STEP_USER_DATA_SCHEMA = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
            }
        )
        # ...
        async def async_step_user(
                self, user_input: dict[str, Any] | None = None
        ):
            # ...
            if user_input is not None:
                info, error = await self._validate_input(user_input[CONF_HOST])
                # ...
        ```
    *   There are no discovery steps implemented in the config flow (e.g., `async_step_zeroconf`, `async_step_ssdp`, `async_step_dhcp`).
    *   The `async_step_reauth` flow is designed to re-validate the connection to the *existing* configured host if authentication or connection fails. It does not attempt to discover a new IP address for the AP.
        ```python
        # config_flow.py
        async def async_step_reauth(self, entry_data: Mapping[str, Any]):
            self._host = entry_data[CONF_HOST] # Uses existing host
            return await self.async_step_reauth_confirm()
        ```
    *   While `_abort_if_unique_id_configured()` is used, it's for preventing duplicate entries of the *same manually entered host*, not for updating a host based on discovery.

Since the integration relies on manual IP configuration for the AP and does not implement any discovery protocol to find the AP, it cannot use discovery information to update the AP's network details. The rule's exception states: "Integrations where the devices can't be discovered are exempt from this rule." In this context, the "device" the integration directly connects to and configures is the AP.

Therefore, the `open_epaper_link` integration is **exempt** from the `discovery-update-info` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 20:58:20. Prompt tokens: 60669, Output tokens: 921, Total tokens: 63072_
