# nest: discovery

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [discovery](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery)                                                     |
| Status | **todo**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `discovery` rule applies to the `nest` integration because Nest devices (thermostats, cameras, doorbells) are network-connected devices whose presence can potentially be detected on the local network, for example, via DHCP. Making the integration discoverable improves the user experience by simplifying the initial setup process.

The `nest` integration attempts to support discovery by including `dhcp` entries in its `manifest.json` file:
```json
  "dhcp": [
    {
      "macaddress": "18B430*"
    },
    {
      "macaddress": "641666*"
    },
    {
      "macaddress": "D8EB46*"
    }
  ],
```
This declaration allows Home Assistant's core DHCP discovery mechanism to identify potential Nest devices based on their MAC addresses and initiate a configuration flow for the `nest` integration.

However, the integration does **not** fully follow the rule because its `config_flow.py` file (as provided) is missing the required `async_step_dhcp` method. When Home Assistant's core DHCP discovery finds a matching device, it will attempt to call `async_step_dhcp` on the `nest` config flow handler. If this method is not implemented, the config flow will fail, likely raising an `AttributeError`.

Therefore, while the intent to be discoverable is present, the implementation is incomplete, leading to a "todo" status.

## Suggestions

To make the `nest` integration compliant with the `discovery` rule, the following changes are recommended:

1.  **Implement `async_step_dhcp` in `config_flow.py`:**
    Add an `async_step_dhcp` method to the `NestFlowHandler` class. This method will be called by Home Assistant when a device matching the DHCP criteria in `manifest.json` is discovered.

    ```python
    # homeassistant/components/nest/config_flow.py
    # ...
    from homeassistant.components import dhcp # Add this import
    # ...

    class NestFlowHandler(
        config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
    ):
        # ... (existing methods)

        async def async_step_dhcp(
            self, discovery_info: dhcp.DhcpServiceInfo
        ) -> ConfigFlowResult:
            """Handle DHCP discovery."""
            _LOGGER.info("Nest device discovered via DHCP: %s", discovery_info)

            # Set a unique ID for this flow based on the MAC address to prevent
            # multiple discovery flows for the same device from appearing simultaneously.
            await self.async_set_unique_id(discovery_info.macaddress)
            self._abort_if_unique_id_configured()

            # Store hostname for user display if needed
            self.context["title_placeholders"] = {
                "name": f"Nest device ({discovery_info.hostname or discovery_info.ipaddress})"
            }

            # The Nest integration requires a complex OAuth2 and project setup.
            # DHCP discovery can primarily serve as a prompt to start this manual setup.
            # We can't fully configure from DHCP info alone.
            #
            # Option 1: Directly proceed to the user setup flow.
            # The `async_step_user` typically leads to `async_step_create_cloud_project`.
            # return await self.async_step_user()

            # Option 2: Show a confirmation step specific to DHCP discovery.
            # This provides a slightly better user experience by acknowledging the discovery.
            return await self.async_step_dhcp_confirm()

        async def async_step_dhcp_confirm(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            """Confirm DHCP discovery and proceed to standard setup."""
            if user_input is not None:
                # User confirmed, proceed to the standard setup flow
                # which starts with cloud project creation.
                return await self.async_step_create_cloud_project()

            # If any Nest config entry (project) is already set up,
            # the discovered device will likely be added automatically by that existing setup
            # once it's online and part of the same Google Account/Project.
            # We could add a check here for `self._async_current_entries()`
            # and potentially inform the user or abort if a setup already exists.
            # However, allowing the user to proceed handles cases where they might
            # be setting up a device for a *different* Nest project.

            return self.async_show_form(
                step_id="dhcp_confirm",
                description_placeholders=self.context.get("title_placeholders", {}),
            )
        # ... (rest of the class)
    ```

2.  **Add translations for the new step (if `dhcp_confirm` is used):**
    If you add `async_step_dhcp_confirm` and `self.async_show_form(step_id="dhcp_confirm", ...)`:
    In `strings.json`, add entries for `dhcp_confirm`:
    ```json
    // homeassistant/components/nest/strings.json
    {
      // ...
      "config": {
        "step": {
          // ... (existing steps)
          "dhcp_confirm": {
            "title": "Nest Device Discovered",
            "description": "A potential Nest device ({name}) was discovered on your network. Would you like to set it up now? This will take you through the standard Nest configuration process."
          }
        },
        // ...
      },
      // ...
    }
    ```

**Why these changes satisfy the rule:**

*   By implementing `async_step_dhcp`, the integration correctly handles the discovery information provided by Home Assistant core when a device is found via DHCP.
*   This prevents the config flow from crashing and instead guides the user towards setting up the integration.
*   Using `await self.async_set_unique_id(discovery_info.macaddress)` and `self._abort_if_unique_id_configured()` within `async_step_dhcp` ensures that if multiple DHCP discovery packets are received for the same device, only one configuration flow instance is initiated or shown to the user, improving the user experience.
*   Even though Nest's setup is complex and cannot be fully automated from DHCP information alone (due to OAuth and Google Cloud Project requirements), initiating the flow and informing the user that a device was found is a significant improvement and fulfills the spirit of the discovery rule.

_Created at 2025-05-28 23:04:25. Prompt tokens: 32939, Output tokens: 1605, Total tokens: 39655_
