# eheimdigital: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [eheimdigital](https://www.home-assistant.io/integrations/eheimdigital/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `reconfiguration-flow` rule requires integrations to provide a way for users to update their configuration settings (e.g., host, API key) without needing to remove and re-add the integration. This is achieved by implementing an `async_step_reconfigure` method in the integration's `config_flow.py`.

This rule applies to the `eheimdigital` integration:
1.  The `manifest.json` file specifies `"config_flow": true`, indicating it uses a config flow for setup.
2.  The `config_flow.py` file shows that the integration has user-configurable settings, specifically `CONF_HOST`:
    ```python
    # homeassistant/components/eheimdigital/config_flow.py
    CONFIG_SCHEMA = vol.Schema(
        {vol.Required(CONF_HOST, default="eheimdigital.local"): selector.TextSelector()}
    )
    ```
    And during the `async_step_user`:
    ```python
    # homeassistant/components/eheimdigital/config_flow.py
    hub = EheimDigitalHub(
        host=user_input[CONF_HOST],
        # ...
    )
    ```

The `eheimdigital` integration currently does **not** follow this rule. A review of its `config_flow.py` (path: `homeassistant/components/eheimdigital/config_flow.py`) reveals that there is no `async_step_reconfigure` method implemented within the `EheimDigitalConfigFlow` class. This means users cannot, for example, change the IP address or hostname of their EHEIM Digital device through the UI once it has been configured, without deleting and re-adding the integration.

## Suggestions

To make the `eheimdigital` integration compliant with the `reconfiguration-flow` rule, the `async_step_reconfigure` method should be added to the `EheimDigitalConfigFlow` class in `homeassistant/components/eheimdigital/config_flow.py`.

This method would allow users to modify the `CONF_HOST` setting. The implementation should:
1.  Retrieve the existing configuration entry.
2.  Present a form to the user, pre-filled with the current `CONF_HOST` value.
3.  Upon submission, validate the new host by attempting to connect to it.
4.  Crucially, verify that the device at the new host is the *same* device by comparing its unique identifier (MAC address for EHEIM Digital) with the unique ID of the existing config entry.
5.  If validation and device identity check are successful, update the config entry with the new host and reload the integration.
6.  Handle any connection errors appropriately.

Here's an example of how `async_step_reconfigure` could be implemented:

```python
# homeassistant/components/eheimdigital/config_flow.py

# ... (import other necessary modules like asyncio, ClientError, EheimDigitalDevice, EheimDigitalHub, selector, etc.)
# from homeassistant.config_entries import ConfigFlowResult
# from homeassistant.const import CONF_HOST
# from homeassistant.helpers.aiohttp_client import async_get_clientsession
# from .const import DOMAIN, LOGGER # Ensure LOGGER is imported if not already
# from eheimdigital.device import EheimDigitalDevice
# from eheimdigital.hub import EheimDigitalHub
# from aiohttp import ClientError
# import asyncio
# from typing import TYPE_CHECKING, Any # Add if not present

class EheimDigitalConfigFlow(ConfigFlow, domain=DOMAIN):
    """The EHEIM Digital config flow."""

    # ... (existing __init__, async_step_zeroconf, async_step_discovery_confirm, async_step_user methods) ...

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        entry = self.config_entry
        errors: dict[str, str] = {}

        if user_input:
            new_host = user_input[CONF_HOST]
            
            # It's good practice to use a new event for each connection attempt in a flow
            # to avoid race conditions if the flow instance's event is reused.
            reconfigure_main_device_event = asyncio.Event()
            hub = EheimDigitalHub(
                host=new_host,
                session=async_get_clientsession(self.hass),
                loop=self.hass.loop,
                main_device_added_event=reconfigure_main_device_event,
            )
            try:
                await hub.connect()
                async with asyncio.timeout(2):  # Use a reasonable timeout
                    await reconfigure_main_device_event.wait()
                
                # Ensure hub.main is populated and is the correct type
                if TYPE_CHECKING: # Or runtime check if hub.main can be None
                    assert isinstance(hub.main, EheimDigitalDevice)
                
                new_mac_address = hub.main.mac_address
                await hub.close()

                if entry.unique_id != new_mac_address:
                    # Add a new translation key for this error
                    errors["base"] = "reconfigure_wrong_device" 
                else:
                    # MAC address matches, it's the same device. Update and reload.
                    # self.hass.config_entries.async_update_entry(entry, data=user_input)
                    # await self.hass.config_entries.async_reload(entry.entry_id)
                    # return self.async_abort(reason="reconfigure_successful")
                    # The above three lines can be replaced by async_update_reload_and_abort:
                    return self.async_update_reload_and_abort(
                        entry,
                        data=user_input, # user_input should contain all data fields like {CONF_HOST: new_host}
                    )
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
                LOGGER.exception("Unknown exception occurred during reconfiguration")
        
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST)): selector.TextSelector(),
                }
            ),
            errors=errors,
            description_placeholders={"name": entry.title}, # Optional: provide context
        )

```

**To complete this implementation, you would also need to:**

*   Add a new translation key `reconfigure_wrong_device` to `strings.json` under `config.error` (or a more suitable place) to inform the user that the device at the new host is not the same as the one being reconfigured. For example:
    ```json
    // homeassistant/components/eheimdigital/strings.json
    {
      "config": {
        // ...
        "error": {
          // ...
          "reconfigure_wrong_device": "The device found at the new host is different from the one originally configured. Please ensure the host is correct for the intended device."
        }
      },
      // ...
    }
    ```

By implementing this `async_step_reconfigure` flow, the `eheimdigital` integration will allow users to conveniently update the device's host address, improving user experience and adhering to the quality scale requirements.

_Created at 2025-05-27 15:42:52. Prompt tokens: 15327, Output tokens: 1837, Total tokens: 21331_
