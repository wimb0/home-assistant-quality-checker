# knx: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [knx](https://www.home-assistant.io/integrations/knx/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `repair-issues` rule mandates that integrations should use repair issues and repair flows to inform users about actionable problems that require their intervention.

The KNX integration currently handles errors during the initial configuration flow (`config_flow.py`) by displaying messages directly in the UI. However, if an already configured integration fails to set up during Home Assistant startup (e.g., the KNX/IP interface is unreachable, a configured IP address is no longer valid, or KNX secure credentials stored in the config entry are incorrect), it raises `ConfigEntryNotReady`. This correctly prevents the integration from loading but does not create a repair issue to guide the user on how to fix the problem through the Home Assistant "Repairs" section. Instead, users typically see a "Retrying setup..." message, which is less informative.

Key areas where repair issues would be beneficial:
1.  **Connection Failures:** In `homeassistant/components/knx/__init__.py`, the `async_setup_entry` function catches `XKNXException` (which is a base class for more specific exceptions like `CommunicationError` or `InvalidSecureConfiguration` from the `xknx` library) and raises `ConfigEntryNotReady`. If these exceptions indicate user-fixable problems (e.g., wrong host/port, interface offline, incorrect KNX secure credentials), a repair issue should be created.
2.  **KNX Secure Issues:** If loading a `.knxkeys` file fails due to an incorrect password or a corrupted file, or if other secure parameters (like backbone key or user credentials) are invalid, these are user-fixable issues. Such errors might be caught as `InvalidSecureConfiguration` or other `XKNXException` subtypes during `knx_module.start()`.

The integration does not currently import `homeassistant.helpers.issue_registry as ir` or make calls to `ir.async_create_issue()`. Furthermore, the `strings.json` file does not contain any `issues.*` translation keys, which are standard for repair issue descriptions.

The `quality_scale.yaml` for the `knx` integration already lists `repair-issues: todo`, which aligns with this assessment.

## Suggestions

To make the KNX integration compliant with the `repair-issues` rule, the following changes are recommended:

1.  **Import Issue Registry:**
    In `homeassistant/components/knx/__init__.py`, add the import:
    ```python
    from homeassistant.helpers import issue_registry as ir
    ```

2.  **Create Repair Issues on Setup Failure:**
    Modify the `async_setup_entry` function in `homeassistant/components/knx/__init__.py` to create repair issues when specific, user-actionable `XKNXException` subtypes occur.

    ```python
    # In homeassistant/components/knx/__init__.py
    # ... other imports
    from xknx.exceptions import CommunicationError, InvalidSecureConfiguration, XKNXException # Ensure these are imported
    from homeassistant.helpers import issue_registry as ir
    from homeassistant.const import CONF_HOST, CONF_PORT # Ensure these are imported
    # ...

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Load a config entry."""
        # ... (existing code for loading YAML config) ...
        config = hass.data.pop(_KNX_YAML_CONFIG, None)
        # ... (rest of config loading logic) ...

        try:
            knx_module = KNXModule(hass, config, entry)
            await knx_module.start()
        except CommunicationError as ex:
            issue_id = f"communication_error_{entry.entry_id}"
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=True, # Assuming reconfigure/options flow can fix this
                learn_more_url="https://www.home-assistant.io/integrations/knx/#connection-problems", # Point to relevant docs
                severity=ir.IssueSeverity.ERROR,
                translation_key="communication_error",
                translation_placeholders={
                    "host": str(entry.data.get(CONF_HOST, "N/A")),
                    "port": str(entry.data.get(CONF_PORT, "N/A")),
                    "error": str(ex)
                },
            )
            raise ConfigEntryNotReady(f"Communication error with KNX interface: {ex}") from ex
        except InvalidSecureConfiguration as ex:
            issue_id = f"secure_config_error_{entry.entry_id}"
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=True, # Options flow for secure settings
                severity=ir.IssueSeverity.ERROR,
                translation_key="secure_config_error",
                translation_placeholders={
                    "knxkeys_filename": entry.data.get(CONF_KNX_KNXKEY_FILENAME, "N/A"),
                    "error": str(ex)
                },
                # Consider adding an issue_handler to directly start the options flow for secure settings
            )
            raise ConfigEntryNotReady(f"KNX secure configuration error: {ex}") from ex
        except XKNXException as ex: # Generic fallback for other XKNX issues during setup
            issue_id = f"generic_xknx_error_{entry.entry_id}"
            # Determine if this should be fixable (e.g., via reconfigure) or if it's informational
            # For now, assume it might be user-fixable through reconfiguration.
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=True,
                severity=ir.IssueSeverity.ERROR,
                translation_key="generic_xknx_error",
                translation_placeholders={"error": str(ex)},
            )
            raise ConfigEntryNotReady(f"KNX setup failed due to XKNXException: {ex}") from ex

        # If setup is successful, clear any previous issues for this entry
        # Use a loop or list for all possible issue_ids if there are many
        for error_type in ["communication_error", "secure_config_error", "generic_xknx_error"]:
            ir.async_delete_issue(hass, DOMAIN, f"{error_type}_{entry.entry_id}")

        hass.data[KNX_MODULE_KEY] = knx_module
        # ... (rest of the successful setup code) ...
        return True
    ```

3.  **Add Translations for Repair Issues:**
    In `homeassistant/components/knx/strings.json` (and its translations, e.g., `en.json`), add an `issues` section:
    ```json
    {
      "config": {
        // ... existing config strings ...
      },
      "options": {
        // ... existing options strings ...
      },
      "issues": {
        "communication_error": {
          "title": "KNX Connection Failed",
          "description": "Home Assistant could not connect to the KNX interface at `{host}:{port}`.\n\nPlease verify:\n- The KNX interface is powered on and connected to the network.\n- The IP address and port are correct in the KNX integration settings.\n- Your Home Assistant instance can reach the KNX interface on the network (check firewalls or routing).\n- If using tunneling, ensure a tunnel slot is available on the interface.\n\nError details: {error}"
        },
        "secure_config_error": {
          "title": "KNX Secure Configuration Error",
          "description": "There was an error with the KNX IP Secure configuration. This could be due to an incorrect password for the KNX Keyring file (`{knxkeys_filename}`), a corrupted keyring file, or invalid secure parameters (backbone key, user credentials).\n\nPlease check the KNX integration options and ensure your KNX Secure settings and/or keyring file are correct.\n\nError details: {error}"
        },
        "generic_xknx_error": {
          "title": "KNX Setup Error",
          "description": "An unexpected error occurred during KNX setup: {error}\n\nPlease check your KNX configuration and the Home Assistant logs for more details. You may need to reconfigure the KNX integration."
        }
        // Add more issue types as identified
      }
      // ... rest of the file ...
    }
    ```

4.  **Consider Repair Flows (Advanced):**
    For issues where `is_fixable=True`, if a specific configuration step can resolve the issue (e.g., re-entering a password, re-selecting a KNX interface), you can implement a repair flow and link it using the `issue_handler` argument in `ir.async_create_issue`. This would guide the user directly to the relevant part of the config or options flow.

By implementing these suggestions, the KNX integration will provide more user-friendly guidance when setup or connection issues occur, directing users to the "Repairs" section in Home Assistant for actionable solutions.

_Created at 2025-05-14 13:40:38. Prompt tokens: 100961, Output tokens: 2187, Total tokens: 107105_
