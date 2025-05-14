# knx: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [knx](https://www.home-assistant.io/integrations/knx/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `repair-issues` rule requires integrations to use repair issues and repair flows when user intervention is needed to fix a problem, making it a user-friendly way to inform and guide the user.

This rule applies to the `knx` integration because its setup and ongoing operation can encounter various issues that are user-fixable. These include:
*   Persistent connection failures (e.g., incorrect IP address/port for the KNX interface, interface offline).
*   KNX Secure configuration problems (e.g., missing or corrupt `.knxkeys` file, incorrect passwords for secure tunneling or routing if these were previously configured and are now failing).
*   Issues with a previously uploaded KNX project file (e.g., if it became missing or corrupted).

The `knx` integration currently does **not** follow this rule.
A review of the codebase shows no usage of `homeassistant.helpers.issue_registry.async_create_issue` (aliased as `ir.async_create_issue`).

Currently, in `homeassistant/components/knx/__init__.py`, the `async_setup_entry` function calls `knx_module.start()`. If this method raises an `XKNXException` (which can happen due to various connection or configuration issues with the underlying `xknx` library), Home Assistant raises `ConfigEntryNotReady`. While this allows Home Assistant to retry the setup, it doesn't provide the user with specific, actionable information on how to resolve persistent problems.

For example:
1.  If a KNX interface's IP address changes after initial setup, `knx_module.start()` would likely fail with a `CommunicationError` (a subclass of `XKNXException`). This currently leads to repeated retries without a clear user-facing explanation or fix path beyond checking logs.
2.  If a `.knxkeys` file, previously uploaded for a secure connection, becomes corrupted or is unintentionally deleted from the storage, `knx_module.start()` (via `xknx` library's secure connection setup) could fail. This also results in `ConfigEntryNotReady`.

These are scenarios where a repair issue, potentially linking to the integration's options flow, would significantly improve the user experience by guiding them to fix the configuration.

The `config_flow.py` handles many errors during the initial setup or options flow by displaying form errors, which is appropriate for that context. Repair issues are more suited for problems detected at startup or during runtime post-configuration.

## Suggestions

To make the `knx` integration compliant with the `repair-issues` rule, consider the following:

1.  **Identify Actionable Failure Points:**
    Focus on errors that can occur during `KNXModule.start()` in `async_setup_entry` (`homeassistant/components/knx/__init__.py`) which are likely user-fixable. These primarily involve persistent connection issues or problems with secure configuration files (like `.knxkeys`).

2.  **Implement `ir.async_create_issue`:**
    In `homeassistant/components/knx/__init__.py`, modify the `async_setup_entry` to catch specific, actionable exceptions from `knx_module.start()` and create repair issues.

    *   Import the issue registry:
        ```python
        from homeassistant.helpers import issue_registry as ir
        ```
    *   Add `strings.json` entries for the new repair issues (see point 4).

    *   Example of handling exceptions:
        ```python
        # In homeassistant/components/knx/__init__.py

        from xknx.exceptions import CommunicationError, InvalidSecureConfiguration # and other relevant XKNXException subclasses

        # ...
        CONF_KNX_KNXKEY_FILENAME = "knxkeys_filename" # Ensure this is imported or defined if used from const.py
        CONF_HOST = "host" # Ensure this is imported or defined
        # ...

        async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
            # ... (existing code) ...
            try:
                knx_module = KNXModule(hass, config, entry)
                await knx_module.start()
            except InvalidSecureConfiguration as ex:
                # Example: If a keyring file was configured but is now problematic
                if entry.data.get(CONF_KNX_KNXKEY_FILENAME):
                    ir.async_create_issue(
                        hass,
                        DOMAIN,
                        "invalid_keyring_file_startup", # Unique ID for this issue
                        is_fixable=True, # Takes user to options flow
                        issue_domain=DOMAIN, # Links to this integration's config entry
                        severity=ir.IssueSeverity.ERROR,
                        translation_key="invalid_keyring_file_startup",
                        translation_placeholders={"error_details": str(ex)},
                    )
                # Still raise ConfigEntryNotReady for retries, but repair issue guides user
                raise ConfigEntryNotReady(f"KNX Secure configuration error: {ex}") from ex
            except CommunicationError as ex:
                # Example: Persistent connection failure
                ir.async_create_issue(
                    hass,
                    DOMAIN,
                    "knx_connection_failure_startup", # Unique ID
                    is_fixable=True,
                    issue_domain=DOMAIN,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="knx_connection_failure_startup",
                    translation_placeholders={
                        "host": entry.data.get(CONF_HOST, "unknown"),
                        "error_details": str(ex),
                    },
                )
                raise ConfigEntryNotReady(f"KNX communication error: {ex}") from ex
            except XKNXException as ex: # Catch-all for other xknx issues
                # Consider if other specific XKNXException types are common and user-fixable
                # For a generic one, you might not set is_fixable=True unless there's a clear path
                _LOGGER.error("Unhandled XKNXException during KNX setup: %s", ex)
                # Optionally, create a generic, non-fixable repair issue if appropriate
                # ir.async_create_issue(
                #     hass,
                #     DOMAIN,
                #     "generic_knx_startup_error",
                #     is_fixable=False,
                #     severity=ir.IssueSeverity.ERROR,
                #     translation_key="generic_knx_startup_error",
                #     translation_placeholders={"error_details": str(ex)},
                # )
                raise ConfigEntryNotReady from ex
            # ... (rest of async_setup_entry) ...
        ```

3.  **Clear `translation_key`s:**
    Use descriptive `translation_key`s for each repair issue type. These keys will be used to look up localized messages in `strings.json`.

4.  **Add Translations:**
    Add entries to `homeassistant/components/knx/strings.json` (and its translations) for the repair issues. For example:
    ```json
    {
      "issues": {
        "invalid_keyring_file_startup": {
          "title": "KNX Keyring File Issue",
          "description": "There was a problem loading the KNX keyring file, which is needed for your secure KNX connection: {error_details}\n\nPlease go to the KNX integration options to re-upload or check your keyring file and password."
        },
        "knx_connection_failure_startup": {
          "title": "KNX Connection Failed",
          "description": "Home Assistant could not connect to your KNX interface at '{host}': {error_details}\n\nPlease check the interface's power, network connection, and IP address. You may need to reconfigure the KNX integration via the options menu."
        },
        "generic_knx_startup_error": {
          "title": "KNX Startup Error",
          "description": "The KNX integration encountered an unexpected error during startup: {error_details}\n\nPlease check your Home Assistant logs for more details. If the problem persists, you might need to review your KNX configuration or report an issue."
        }
        // ... other repair issues
      }
    }
    ```

5.  **Leverage Options Flow:**
    Since `is_fixable=True` and `issue_domain=DOMAIN` are used, the repair issue will offer a "RECONFIGURE" button. This button will take the user to the KNX integration's options flow (`KNXOptionsFlow` in `config_flow.py`). Ensure the options flow provides the necessary steps to correct the identified issues (e.g., re-uploading a keyring file, changing connection parameters). The KNX integration already has a comprehensive options flow, which is a good starting point.

By implementing these suggestions, the `knx` integration will provide a more user-friendly experience when encountering common, fixable problems, aligning with the `repair-issues` quality scale rule.

_Created at 2025-05-14 11:38:32. Prompt tokens: 100961, Output tokens: 2149, Total tokens: 107512_
