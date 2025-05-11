# wled: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **todo**                                       |
| Reason | N/A |

## Overview

The `reconfiguration-flow` rule requires integrations to provide a way for users to update configuration settings (like an IP address or API key) without needing to delete and re-add the integration. This is typically achieved by implementing an `async_step_reconfigure` method in the integration's `ConfigFlow`.

The WLED integration's configuration flow (`config_flow.py`) primarily uses the `CONF_HOST` (IP address or hostname of the WLED device) for setup. This is a setting that can change, for example, if the device gets a new IP address from DHCP.

Looking at the `wled/config_flow.py` file, the `WLEDFlowHandler` class handles the initial setup:
```python
# wled/config_flow.py
class WLEDFlowHandler(ConfigFlow, domain=DOMAIN):
    # ...
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors = {}

        if user_input is not None:
            try:
                device = await self._async_get_device(user_input[CONF_HOST])
            except WLEDConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    device.info.mac_address, raise_on_progress=False
                )
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: user_input[CONF_HOST]}
                )
                return self.async_create_entry(
                    title=device.info.name,
                    data={
                        CONF_HOST: user_input[CONF_HOST], # Host is stored in data
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}), # Host is a configurable setting
            errors=errors or {},
        )
    # ...
```
The `CONF_HOST` is a key piece of data stored for the integration. However, the `WLEDFlowHandler` class does not implement the `async_step_reconfigure` method. If a WLED device's IP address changes, the user currently has no UI-driven way to update this host for the existing configuration entry and would need to remove and re-add the integration.

The exception to this rule ("Integrations that don't have settings in their configuration flow are exempt") does not apply here, as `CONF_HOST` is clearly a setting in the configuration flow.

Therefore, the WLED integration does not currently follow the `reconfiguration-flow` rule.

## Suggestions

To make the `wled` integration compliant with the `reconfiguration-flow` rule, an `async_step_reconfigure` method should be added to the `WLEDFlowHandler` class in `config_flow.py`. This method would allow users to update the host of an already configured WLED device.

Here's a conceptual implementation:

1.  **Add `async_step_reconfigure` to `WLEDFlowHandler`:**

    ```python
    # wled/config_flow.py

    # ... (other imports)
    from homeassistant.exceptions import HomeAssistantError # For a custom error key

    class WLEDFlowHandler(ConfigFlow, domain=DOMAIN):
        """Handle a WLED config flow."""

        VERSION = 1
        # ... (existing attributes and methods)

        async def async_step_reconfigure(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            """Handle reconfiguration of the WLED device host."""
            entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
            assert entry  # entry_id is always set in reconfigure context

            errors: dict[str, str] = {}

            if user_input is not None:
                new_host = user_input[CONF_HOST]
                try:
                    # Validate the new host and get device info
                    device_at_new_host = await self._async_get_device(new_host)
                except WLEDConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    # Ensure the device at the new host is the same as the original one
                    # by comparing their unique IDs (MAC addresses for WLED).
                    if device_at_new_host.info.mac_address != entry.unique_id:
                        errors["base"] = "reconfigure_mismatch" # Or a more specific error key
                    else:
                        # Update the config entry with the new host
                        return self.async_update_reload_and_abort(
                            entry,
                            data={**entry.data, CONF_HOST: new_host},
                            reason="reconfigure_successful",
                        )
            else:
                # Pre-fill the form with the current host
                user_input = {CONF_HOST: entry.data[CONF_HOST]}

            return self.async_show_form(
                step_id="reconfigure",
                data_schema=vol.Schema({vol.Required(CONF_HOST, default=user_input.get(CONF_HOST)): str}),
                errors=errors,
                description_placeholders={"name": entry.title}, # Optional: provide context
            )

        # ... (rest of the class)
    ```

2.  **Add a new error string for mismatch (optional but good practice):**
    Update `strings.json` (and its translations) if you use a custom error key like `reconfigure_mismatch`.
    Example for `strings.json`:
    ```json
    {
      "config": {
        // ...
        "error": {
          "cannot_connect": "[%key:common::config_flow::error::cannot_connect%]",
          "reconfigure_mismatch": "The device found at the new host is different from the original one. Please ensure the host is correct for the device '{name}'."
        },
        // ...
      }
      // ...
    }
    ```
    If using a common error, this step might not be needed, but a specific message is more user-friendly.

**Explanation of Changes:**
*   The `async_step_reconfigure` method is standard for allowing reconfiguration.
*   It retrieves the current `ConfigEntry`.
*   It presents a form to the user, pre-filled with the current `CONF_HOST`.
*   When the user submits a new host, it attempts to connect to the WLED device at the new host using the existing `_async_get_device` helper.
*   **Crucially**, it verifies that the unique ID (MAC address) of the device at the new host matches the unique ID of the existing configuration entry. This prevents the user from accidentally reconfiguring the entry to point to a completely different WLED device.
*   If validation passes and the device matches, `self.async_update_reload_and_abort` is called to update the entry's data with the new host and reload the integration.
*   Appropriate error handling for connection issues or device mismatch is included.

By implementing this, users will be able to update the IP address of their WLED devices through the UI without needing to delete and re-add them, fulfilling the requirements of the `reconfiguration-flow` rule.

_Created at 2025-05-10 23:05:35. Prompt tokens: 23267, Output tokens: 1803, Total tokens: 26886_
