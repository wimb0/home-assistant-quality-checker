# knx: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [knx](https://www.home-assistant.io/integrations/knx/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `repair-issues` rule requires integrations to use repair issues and repair flows to inform users about problems they can fix. This rule applies to the KNX integration because:
1.  KNX integration relies on communication with external hardware (KNX IP interfaces/routers) and potentially complex configurations (IP addresses, ports, individual addresses, KNX project files, security keys).
2.  Errors in these configurations or changes in the KNX environment (e.g., IP address change of the interface, corrupted project file, incorrect security credentials) can lead to persistent failures.
3.  Many of these failures are user-correctable by modifying the integration's configuration, re-uploading files, or checking the external KNX hardware.

The KNX integration currently does **not** follow this rule. A review of the codebase, particularly `homeassistant/components/knx/__init__.py` and related files, shows no usage of the `homeassistant.helpers.issue_registry.async_create_issue` function or any repair flow mechanisms.

For instance, in `homeassistant/components/knx/__init__.py`, the `async_setup_entry` function catches generic `XKNXException` during the setup process and raises `ConfigEntryNotReady`:
```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # ...
    try:
        knx_module = KNXModule(hass, config, entry)
        await knx_module.start()
    except XKNXException as ex: # <<< This is a key area
        raise ConfigEntryNotReady from ex
    # ...
```
While `ConfigEntryNotReady` leads to retries, it doesn't provide specific, actionable guidance to the user via the UI's "Repairs" section. If the underlying `XKNXException` (or other exceptions like `XknxProjectException` from project file parsing) indicates a user-fixable problem (e.g., `CommunicationError` due to a wrong IP, `InvalidSecureConfiguration` for key issues, or a faulty project file), a repair issue should be created to guide the user.

## Suggestions

To make the KNX integration compliant with the `repair-issues` rule, the following changes are recommended:

1.  **Identify User-Fixable Exceptions:**
    Determine which specific exceptions caught during setup (primarily in `async_setup_entry` but potentially also during runtime if persistent issues arise) indicate problems that the user can resolve. Examples include:
    *   `xknx.exceptions.CommunicationError`: If the KNX IP interface is unreachable due to a misconfigured IP/port or if the interface is offline.
    *   `xknx.exceptions.InvalidSecureConfiguration`: If KNX Secure is enabled and there are issues with keys or passwords.
    *   `xknx.exceptions.CouldNotParseAddress`: If the configured individual address is invalid.
    *   `xknxproject.exceptions.XknxProjectException` (or similar): If a loaded KNX project file is corrupted, password-protected without a password, or has other parsing issues.

2.  **Implement Repair Issue Creation:**
    In `homeassistant/components/knx/__init__.py`, modify the `async_setup_entry` function to catch these specific exceptions. For each, use `homeassistant.helpers.issue_registry.async_create_issue` to create a repair issue.

    Example modification:
    ```python
    # In homeassistant/components/knx/__init__.py
    # Add necessary imports
    from homeassistant.helpers import issue_registry as ir
    from xknx.exceptions import CommunicationError, InvalidSecureConfiguration # and others

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        # ...
        try:
            knx_module = KNXModule(hass, config, entry)
            await knx_module.start()
        except CommunicationError as ex:
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"communication_error_{entry.entry_id.replace('.', '_')}", # Unique issue ID
                is_fixable=True,
                issue_domain=DOMAIN, # To link with a potential RepairsFlow
                severity=ir.IssueSeverity.ERROR,
                translation_key="communication_error",
                translation_placeholders={
                    "error": str(ex),
                    "host": entry.data.get(CONF_HOST, "unknown"), # Example placeholder
                },
                learn_more_url="https://www.home-assistant.io/integrations/knx/#troubleshooting" # Example URL
            )
            raise ConfigEntryNotReady(f"Communication error with KNX interface: {ex}") from ex
        except InvalidSecureConfiguration as ex:
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"invalid_secure_config_{entry.entry_id.replace('.', '_')}",
                is_fixable=True,
                issue_domain=DOMAIN,
                severity=ir.IssueSeverity.ERROR,
                translation_key="invalid_secure_config",
                translation_placeholders={"error": str(ex)},
                learn_more_url="https://www.home-assistant.io/integrations/knx/#knx-ip-secure"
            )
            raise ConfigEntryNotReady(f"Invalid KNX Secure configuration: {ex}") from ex
        # Add more specific exception handlers as needed
        except XKNXException as ex: # Catch-all for other XKNX issues
            # For non-specific XKNXException, consider if it's always user-fixable
            # or if some should remain just ConfigEntryNotReady or be non-fixable issues.
            # As a start, one might make this a non-fixable informative issue:
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"generic_xknx_error_{entry.entry_id.replace('.', '_')}",
                is_fixable=False, # Or True if a general "check config" repair flow exists
                severity=ir.IssueSeverity.ERROR,
                translation_key="generic_xknx_error",
                translation_placeholders={"error": str(ex)},
            )
            raise ConfigEntryNotReady(f"KNX setup failed: {ex}") from ex
        # ...
    ```

3.  **Add Translation Strings:**
    Add new entries to `homeassistant/components/knx/strings.json` (and its translations) for the `translation_key`s used (e.g., `communication_error`, `invalid_secure_config`, `generic_xknx_error`).

4.  **Implement a `RepairsFlow`:**
    Create a new file `homeassistant/components/knx/repairs.py`. This file will contain a class inheriting from `RepairsFlow` that handles the `issue_id`s created.
    For issues related to configuration (like wrong IP, port, or security credentials), the repair flow should typically guide the user to the integration's options flow to correct the settings.

    Example structure for `repairs.py`:
    ```python
    # In homeassistant/components/knx/repairs.py
    from homeassistant.components.repairs import RepairsFlow
    from homeassistant.core import HomeAssistant
    from homeassistant.data_entry_flow import FlowResult

    class KnxRepairsFlow(RepairsFlow):
        """Handler for KNX repair flow."""

        async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
            """Handle the first step of a repair flow."""
            # issue_id is available in self.issue_id
            # config_entry_id is available in self.config_entry_id
            if self.issue_id.startswith("communication_error_") or \
               self.issue_id.startswith("invalid_secure_config_"):
                # For these issues, redirect to the options flow of the config entry
                return await self.async_step_reconfigure()
            # Add other issue_id handling if needed
            return self.async_abort(reason="unknown_repair_issue")

        async def async_step_reconfigure(self, user_input: dict | None = None) -> FlowResult:
            """Handles the reconfiguration confirm step."""
            if user_input is not None:
                # Assuming the config_entry_id is set correctly when the issue was created
                return self.async_create_entry(
                    title="", # Not needed, options flow has its own title
                    data={},   # No data to pass, options flow will load current config
                    handler=self.config_entry.options.handler # Points to KNXOptionsFlow
                )

            return self.async_show_form(
                step_id="reconfigure",
                description_placeholders={"issue_id": self.issue_id},
                # data_schema can be empty if it's just a confirmation
            )

    async def async_create_fix_flow(
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> RepairsFlow:
        """Create flow."""
        return KnxRepairsFlow()
    ```
    *   The `async_create_fix_flow` function needs to be registered. This is typically done in `__init__.py` by setting `hass.data[DOMAIN_DATA]["repairs_flow"] = async_create_fix_flow` or by registering it with `repairs.async_register_repair_flow`. The modern way is often to just have the `async_create_fix_flow` in `repairs.py` and Home Assistant discovers it.
    *   The `translation_key` for `RepairsFlow` steps should also be added to `strings.json`.

5.  **Consider Project File Issues:**
    If `knx_module.project.load_project()` (called within `KNXModule.start()`) can fail due to a user-fixable issue with the KNX project file (e.g., corrupted after storage, password changed), catch the relevant `XknxProjectException` and create a repair issue. The repair flow might guide the user to re-upload the project file via the KNX panel or options flow.

By implementing these suggestions, the KNX integration will provide a more user-friendly experience when configuration or runtime issues occur, guiding users towards resolving them.

_Created at 2025-05-14 11:37:13. Prompt tokens: 100961, Output tokens: 2490, Total tokens: 107968_
