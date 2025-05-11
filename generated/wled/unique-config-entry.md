# wled: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `unique-config-entry` rule requires that an integration prevents the same device or service from being set up multiple times. This is typically achieved by assigning a unique identifier to the configuration entry or by ensuring that certain configuration data (like a host) is unique.

This rule applies to the `wled` integration as it uses a config flow to set up WLED devices, and users could potentially attempt to add the same device multiple times.

The `wled` integration correctly follows this rule by using the device's MAC address as a `unique_id` for the config entry. This ensures that each WLED device can only be configured once.

Specifically, in `config_flow.py`:

1.  **User-initiated flow (`async_step_user`)**:
    *   The integration fetches device information, including its MAC address, using `await self._async_get_device(user_input[CONF_HOST])`.
    *   It then sets this MAC address as the unique ID for the config entry: `await self.async_set_unique_id(device.info.mac_address, raise_on_progress=False)`.
    *   Crucially, it then calls `self._abort_if_unique_id_configured(updates={CONF_HOST: user_input[CONF_HOST]})`. This method checks if a config entry with the same unique ID already exists. If so, it aborts the flow, preventing a duplicate setup. The `updates` parameter allows the host to be updated if the device (identified by its unique MAC) is found at a new IP address.

    ```python
    # config_flow.py
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # ...
            else:
                await self.async_set_unique_id(
                    device.info.mac_address, raise_on_progress=False
                )
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: user_input[CONF_HOST]}
                )
                return self.async_create_entry(
                    # ...
                )
    ```

2.  **Zeroconf discovery flow (`async_step_zeroconf`)**:
    *   The integration attempts to get the MAC address from Zeroconf properties. If available, it sets it as the unique ID: `await self.async_set_unique_id(mac)`.
    *   If not available from properties, it fetches device information (which includes the MAC address) similar to the user flow: `self.discovered_device = await self._async_get_device(discovery_info.host)` and then `await self.async_set_unique_id(self.discovered_device.info.mac_address)`.
    *   In both cases within the Zeroconf flow, it calls `self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.host})` to prevent duplicates and allow host updates for already configured devices.

    ```python
    # config_flow.py
    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        if mac := discovery_info.properties.get(CONF_MAC):
            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured(
                updates={CONF_HOST: discovery_info.host}
            )
        # ... (else block for fetching device if MAC not in properties)
        else:
            # ...
            await self.async_set_unique_id(self.discovered_device.info.mac_address)
            self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.host})
        # ...
    ```

This implementation aligns with the "Unique identifier" method described in the rule documentation, ensuring that each WLED device, identified by its MAC address, can only be configured once in Home Assistant.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:31:12. Prompt tokens: 23814, Output tokens: 1036, Total tokens: 26053_
