# knx: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [knx](https://www.home-assistant.io/integrations/knx/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `repair-issues` rule requires integrations to use repair issues and repair flows to inform users about actionable problems that need their intervention. Repair issues should be informative and guide the user, while repair flows can help fix the problem.

This rule applies to the `knx` integration because there are several scenarios during setup or runtime where user intervention might be necessary to resolve issues. These include connection failures to the KNX gateway/router, invalid KNX secure configurations (e.g., incorrect `.knxkeys` file or passwords), or other XKNX library errors encountered during startup.

Currently, the `knx` integration handles exceptions during the startup of the XKNX library (e.g., in `KNXModule.start()`) by catching `XKNXException` and raising `ConfigEntryNotReady`. This causes Home Assistant to retry the setup, but it does not create a persistent, user-visible repair issue that explains the problem and suggests potential user actions.

Specifically, in `homeassistant/components/knx/__init__.py`, the `KNXModule.start()` method has a `try...except XKNXException` block:
```python
# homeassistant/components/knx/__init__.py
# In class KNXModule:
    async def start(self) -> None:
        """Start XKNX object. Connect to tunneling or Routing device."""
        await self.project.load_project(self.xknx)
        await self.config_store.load_data()
        await self.telegrams.load_history()
        await self.xknx.start() # This can raise XKNXException
```
And `async_setup_entry` calls this:
```python
# homeassistant/components/knx/__init__.py
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # ...
    try:
        knx_module = KNXModule(hass, config, entry)
        await knx_module.start()
    except XKNXException as ex: # This exception is now caught and handled within knx_module.start() as per suggestion
        raise ConfigEntryNotReady from ex # Original code just raises ConfigEntryNotReady
    # ...
```
While `ConfigEntryNotReady` is appropriate for retrying, it doesn't leverage the repair system to provide clear, actionable feedback to the user about *why* the setup is failing and what they might do about it. No calls to `homeassistant.helpers.issue_registry.async_create_issue` are present in the codebase for these startup errors.

## Suggestions

To comply with the `repair-issues` rule, the `knx` integration should create repair issues when specific, potentially user-actionable errors occur during the KNX system startup.

1.  **Import necessary modules** in `homeassistant/components/knx/__init__.py`:
    ```python
    from homeassistant.helpers import issue_registry as ir
    # ConfigEntryNotReady is already imported
    from xknx.exceptions import CommunicationError, InvalidSecureConfiguration # XKNXException is also already imported
    ```

2.  **Modify `KNXModule.start()`** in `homeassistant/components/knx/__init__.py` to catch specific exceptions and create repair issues before re-raising `ConfigEntryNotReady`:

    ```python
    # In class KNXModule within homeassistant/components/knx/__init__.py
    async def start(self) -> None:
        """Start XKNX object. Connect to tunneling or Routing device."""
        await self.project.load_project(self.xknx)
        await self.config_store.load_data()
        await self.telegrams.load_history()
        try:
            await self.xknx.start()
        except InvalidSecureConfiguration as ex:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "secure_config_invalid",
                is_fixable=True,  # User can fix via options flow
                issue_domain=DOMAIN,
                severity=ir.IssueSeverity.ERROR,
                translation_key="secure_config_invalid",
                translation_placeholders={"error": str(ex)},
                # Consider adding: learn_more_url="/integrations/knx/#knx-ip-secure" (adjust URL)
            )
            raise ConfigEntryNotReady(f"KNX Secure configuration error: {ex}") from ex
        except CommunicationError as ex:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "connection_error",
                is_fixable=False,  # User has to fix external network/gateway issue
                issue_domain=DOMAIN,
                severity=ir.IssueSeverity.ERROR,
                translation_key="connection_error",
                translation_placeholders={"error": str(ex)},
            )
            raise ConfigEntryNotReady(f"KNX communication error: {ex}") from ex
        except XKNXException as ex:  # Catch-all for other XKNX errors during start
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "generic_xknx_start_error",
                is_fixable=False,
                issue_domain=DOMAIN,
                severity=ir.IssueSeverity.ERROR,
                translation_key="generic_xknx_start_error",
                translation_placeholders={"error": str(ex)},
            )
            raise ConfigEntryNotReady(f"KNX failed to start: {ex}") from ex
    ```
    The `async_setup_entry` function should then re-raise `ConfigEntryNotReady` if `knx_module.start()` raises it, ensuring the retry mechanism still works. The current `async_setup_entry` structure is mostly fine if `KNXModule.start()` handles its own specific exceptions and repair issue creation.

3.  **Add translation strings** for these repair issues in `homeassistant/components/knx/strings.json` (or `translations/en.json` and other languages):

    ```json
    {
      "config": {
        // ... existing config strings ...
      },
      "options": {
        // ... existing options strings ...
      },
      "entity": {
        // ... existing entity strings ...
      },
      "device_automation": {
        // ... existing device_automation strings ...
      },
      "services": {
        // ... existing services strings ...
      },
      "repairs": {
        "secure_config_invalid": {
          "title": "KNX Secure Configuration Error",
          "description": "Failed to initialize KNX due to a secure configuration problem: `{error}`.\n\nPlease check your KNX Secure settings. If you are using a `.knxkeys` file, ensure it is valid and the password is correct. You may need to re-upload it via the KNX integration options.\n\nIf using manual secure configuration (for routing or tunneling), verify the entered credentials (backbone key, user ID, passwords).",
          "issue_information": "Click 'Fix Issue' to be guided on how to update your KNX Secure configuration via the integration options."
        },
        "connection_error": {
          "title": "KNX Connection Error",
          "description": "Home Assistant could not connect to the KNX bus or interface: `{error}`.\n\nPlease verify:\n- The KNX interface (gateway/router) is powered on and connected to the network.\n- The configured IP address and port are correct for your KNX interface.\n- Network connectivity between Home Assistant and the KNX interface (e.g., firewall, VLANs).\n- If using tunneling, ensure a tunnel slot is available on the interface.\n- If using routing, ensure multicast is correctly configured on your network and the individual address for Home Assistant is not conflicting."
        },
        "generic_xknx_start_error": {
          "title": "KNX Initialization Error",
          "description": "An unexpected error occurred while starting the KNX integration: `{error}`.\n\nPlease check your Home Assistant logs for more details. You may need to review your KNX configuration or the KNX bus itself."
        }
      }
    }
    ```

4.  **(Optional but Recommended for `is_fixable=True`) Implement a basic repair flow** in `homeassistant/components/knx/config_flow.py` for the `secure_config_invalid` issue. This flow would guide the user to the existing options flow where they can update their KNX Secure settings.
    ```python
    # In homeassistant/components/knx/config_flow.py
    from homeassistant.components.repairs import RepairsFlow # Add this import

    # ... (existing imports and code) ...

    class KNXRepairsFlow(RepairsFlow):
        """Handler for KNX repair flow."""

        async def async_step_init(
            self, user_input: dict[str, str] | None = None
        ) -> ConfigFlowResult:
            """Handle the first step of a repair flow."""
            if self.issue_id == "secure_config_invalid":
                return await self.async_step_confirm_reconfigure_secure()
            return self.async_abort(reason="unknown_repair_issue")

        async def async_step_confirm_reconfigure_secure(
            self, user_input: dict[str, str] | None = None
        ) -> ConfigFlowResult:
            """Handle step to guide user to options flow for secure config."""
            if user_input is not None:
                # User clicked "Submit" on the repair step.
                # The actual fix happens in the options flow.
                # We can remove the issue here, or let it be re-evaluated on next startup.
                # For simplicity, let's assume the user will attempt the fix.
                # The issue will be re-created if the problem persists on next HA restart/entry reload.
                return self.async_create_entry(title="", data={})

            # Find the existing KNX config entry
            # KNX is single_config_entry, so there should be at most one.
            knx_entries = self.hass.config_entries.async_entries(DOMAIN)
            if not knx_entries:
                # Should not happen if a repair issue for KNX exists
                return self.async_abort(reason="no_knx_config_entry")
            
            config_entry_id = knx_entries[0].entry_id

            # This will show a confirmation step in the repairs UI.
            # The description comes from strings.json `repairs.secure_config_invalid.issue_information`.
            # The submit button text can be customized or defaults to "Submit".
            return self.async_show_form(
                step_id="confirm_reconfigure_secure",
                # The actual description text from strings.json is used for the issue itself.
                # This description_placeholders can provide additional dynamic info to the form step.
                description_placeholders={
                    "options_flow_path": f"/config/integrations/integration/{DOMAIN}"
                                         f"?config_entry={config_entry_id}" # Path to options flow
                },
                # data_schema=vol.Schema({}), # No input fields needed for this step
            )

    # Also, register this repair flow handler in homeassistant/components/knx/__init__.py:
    # from .config_flow import KNXRepairsFlow
    #
    # async def async_create_repair_flow_handler(entry: ConfigEntry | None) -> RepairsFlow:
    #     """Create a repair flow handler."""
    #     return KNXRepairsFlow()
    ```
    And adjust the `strings.json` for `secure_config_invalid.issue_information` to better guide the user based on how the repair flow step is presented. For example:
    ```json
    "issue_information": "Your KNX Secure configuration is invalid. Click 'Submit' to acknowledge this issue. You will then need to navigate to the KNX integration options (at {options_flow_path}) to correct your settings (e.g., re-upload `.knxkeys` file or update manual credentials)."
    ```

By implementing these changes, the `knx` integration will provide more user-friendly error reporting for common startup problems, aligning with the `repair-issues` quality scale rule.

_Created at 2025-05-14 11:42:04. Prompt tokens: 100961, Output tokens: 2923, Total tokens: 112635_
