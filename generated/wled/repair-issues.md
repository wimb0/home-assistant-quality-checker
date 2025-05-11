# wled: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `repair-issues` rule states that repair issues and repair flows should be used when user intervention is needed to resolve a problem with an integration, particularly when the issue is actionable by the user. These notifications should be informative and guide the user towards a fix.

This rule applies to the `wled` integration. WLED devices run firmware that can become outdated. If a WLED device's firmware version is too old, it might lack features or contain bugs that prevent the Home Assistant integration from functioning correctly or optimally. In such cases, user intervention (updating the WLED firmware) is required.

The `wled` integration currently does not implement the `issue_registry` to create repair issues for such scenarios.
A search for `ir.async_create_issue` or `issue_registry.async_create_issue` in the provided codebase yields no results. While the integration handles connection errors (e.g., `WLEDConnectionError` in `helpers.py` leading to `HomeAssistantError` or `UpdateFailed` in `coordinator.py`), these are general error handling mechanisms. They do not provide specific, user-friendly guidance for actionable issues like outdated firmware.

For example, if the WLED firmware is below a minimum required version for the integration to work properly:
*   In `__init__.py` during `async_setup_entry`, after the initial data fetch (`await entry.runtime_data.async_config_entry_first_refresh()`), the firmware version (`coordinator.data.info.version`) is available.
*   Currently, there's no check against a minimum supported version that would trigger a repair issue. The rule's example directly addresses this "outdated_version" scenario.

The integration does include an `UpdateEntity` (`update.py`), which allows users to update WLED firmware through Home Assistant. This is the mechanism to *perform* the fix. A repair issue would be the mechanism to *inform* the user that such a fix is *necessary* due to incompatibility or malfunction caused by an old firmware version.

Therefore, the `wled` integration does not currently follow the `repair-issues` rule as it misses opportunities to proactively inform users about specific, actionable problems like outdated WLED firmware using the repair issue system.

## Suggestions

To comply with the `repair-issues` rule, the `wled` integration should implement checks for known actionable issues, primarily outdated WLED firmware, and use the `issue_registry` to inform users.

1.  **Define a Minimum Supported WLED Firmware Version:**
    Determine if there's a minimum version of WLED firmware that the integration requires for stable and full-featured operation. This could be a constant, e.g., `MINIMUM_SUPPORTED_WLED_VERSION`.

2.  **Implement Firmware Version Check in `async_setup_entry`:**
    In `__init__.py`, within the `async_setup_entry` function, after the initial data refresh fetches the device information:
    *   Access the device's firmware version (e.g., `coordinator.data.info.version`).
    *   Compare this version against `MINIMUM_SUPPORTED_WLED_VERSION`.

3.  **Create a Repair Issue if Firmware is Outdated:**
    If the firmware version is older than the minimum required:
    *   Import `homeassistant.helpers.issue_registry as ir`.
    *   Call `ir.async_create_issue()` to log the problem.

    Example snippet for `__init__.py`'s `async_setup_entry`:
    ```python
    # In __init__.py

    # At the top with other imports
    from homeassistant.helpers import issue_registry as ir
    from awesomeversion import AwesomeVersion # For version comparison

    # Define this constant appropriately
    MINIMUM_SUPPORTED_WLED_VERSION = AwesomeVersion("0.13.0") # Example version

    async def async_setup_entry(hass: HomeAssistant, entry: WLEDConfigEntry) -> bool:
        """Set up WLED from a config entry."""
        coordinator = WLEDDataUpdateCoordinator(hass, entry=entry)
        entry.runtime_data = coordinator # Store coordinator on entry
        await coordinator.async_config_entry_first_refresh()

        # Check for outdated firmware
        current_version_str = str(coordinator.data.info.version)
        current_version = AwesomeVersion(current_version_str)

        if current_version < MINIMUM_SUPPORTED_WLED_VERSION:
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"outdated_firmware_{entry.unique_id}", # Unique issue ID per device
                is_fixable=False, # User needs to update WLED firmware externally or via HA's update entity
                severity=ir.IssueSeverity.WARNING, # Or ERROR if functionality is severely impacted
                translation_key="outdated_firmware",
                translation_placeholders={
                    "device_name": coordinator.data.info.name,
                    "version": current_version_str,
                    "minimum_version": str(MINIMUM_SUPPORTED_WLED_VERSION),
                    "learn_more_url": "https://kno.wled.ge/basics/upgrading/", # Link to WLED update guide
                },
                # Consider if raising ConfigEntryError is also needed to halt setup.
                # If the integration can still offer partial functionality, a repair issue
                # might be sufficient without raising ConfigEntryError.
            )
            # Example: if critical, prevent full setup (aligns with rule's example)
            # raise ConfigEntryError(
            #     f"WLED firmware version {current_version_str} on '{coordinator.data.info.name}'"
            #     f" is outdated. Minimum required: {MINIMUM_SUPPORTED_WLED_VERSION}."
            #     " Please update WLED firmware."
            # )

        # Set up all platforms for this device/entry.
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Reload entry when its updated.
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))

        return True
    ```

4.  **Add Translations for the Repair Issue:**
    In `strings.json` (and other translation files), add entries for the repair issue:
    ```json
    // In strings.json (or en.json)
    {
      // ... other strings ...
      "issues": {
        "outdated_firmware": {
          "title": "WLED Firmware Update Recommended for {device_name}",
          "description": "The WLED device '{device_name}' is running firmware version {version}, but version {minimum_version} or newer is recommended for optimal compatibility with Home Assistant.\n\nPlease update your WLED device's firmware. You may be able to use the 'Update' entity in Home Assistant for this device, or update directly via the WLED web interface.\n\n[Learn more about updating WLED]({learn_more_url})"
        }
      }
    }
    ```
    Adjust the `translation_key` in `async_create_issue` to match the path in `strings.json` (e.g., `outdated_firmware` if placed directly under `issues`). The placeholders used in `translation_placeholders` must match those in the description string.

5.  **Consider Other Actionable Issues:**
    Review if there are other scenarios where a WLED device might be in a state that requires user intervention (e.g., specific configurations known to cause issues that the user can change) and if repair issues would be appropriate for them. The "cct_unsupported" case is currently handled as a config flow abort, which is correct during initial setup. If such a state could arise *after* setup, a repair issue might be considered.

By implementing these suggestions, the `wled` integration will better adhere to the `repair-issues` rule, providing users with clearer, actionable information when their WLED devices require attention for optimal Home Assistant integration.

_Created at 2025-05-10 23:06:44. Prompt tokens: 21209, Output tokens: 1914, Total tokens: 27611_
