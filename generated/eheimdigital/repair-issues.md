# eheimdigital: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [eheimdigital](https://www.home-assistant.io/integrations/eheimdigital/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `repair-issues` rule requires integrations to use repair issues or repair flows when user intervention is needed to resolve a problem. These issues should be actionable and informative.

This rule applies to the `eheimdigital` integration because it interacts with physical EHEIM devices (filters, heaters, etc.) that can report specific error conditions requiring user action. For example, a filter might report a "rotor stuck" or "air in filter" error, which the user can often resolve by cleaning the device or bleeding air.

Currently, the `eheimdigital` integration does **not** follow this rule. While it does expose device error codes via a sensor (e.g., `sensor.py` creates a sensor for `error_code` from `EheimDigitalClassicVario`), it does not utilize the Home Assistant `issue_registry` to create repair issues for these actionable errors. Users might see the error state on a sensor, but a repair issue would provide a more direct and prominent notification that user intervention is required.

No instances of `homeassistant.helpers.issue_registry.async_create_issue` (or `ir.async_create_issue`) are found in the codebase. The integration handles initial connection failures in `coordinator.py` (`_async_setup`) by raising `ConfigEntryNotReady` and update failures (`_async_update_data`) by raising `UpdateFailed`. These are appropriate for general connectivity issues, but device-specific, actionable errors reported by the device itself are not escalated to repair issues.

For instance, the `strings.json` file defines user-facing messages for error codes:
```json
"error_code": {
  "name": "Error code",
  "state": {
    "no_error": "No error",
    "rotor_stuck": "Rotor stuck",
    "air_in_filter": "Air in filter"
  }
}
```
When "rotor_stuck" or "air_in_filter" conditions occur, a repair issue would be a more user-friendly way to highlight the problem and guide the user, as per the rule's intent.

## Suggestions

To make the `eheimdigital` integration compliant with the `repair-issues` rule, the following steps are recommended:

1.  **Import `issue_registry`:**
    In `homeassistant/components/eheimdigital/coordinator.py`, add the import:
    ```python
    from homeassistant.helpers import issue_registry as ir
    ```

2.  **Implement Issue Creation/Deletion in `_async_update_data`:**
    Modify the `EheimDigitalUpdateCoordinator._async_update_data` method to check for actionable error states from devices after a successful data fetch. If an actionable error is detected, create a repair issue. If the error is resolved, delete the corresponding issue.

    Here's an conceptual example for `EheimDigitalClassicVario` devices:

    ```python
    # In homeassistant/components/eheimdigital/coordinator.py
    # ... (other imports)
    from homeassistant.helpers import issue_registry as ir
    from eheimdigital.types import FilterErrorCode # Assuming FilterErrorCode is accessible
    from eheimdigital.classic_vario import EheimDigitalClassicVario # For isinstance check
    # ...

    class EheimDigitalUpdateCoordinator(
        DataUpdateCoordinator[dict[str, EheimDigitalDevice]]
    ):
        # ... (existing code)

        async def _async_update_data(self) -> dict[str, EheimDigitalDevice]:
            try:
                await self.hub.update()
            except ClientError as ex:
                # This handles general update failures, which is fine.
                # A persistent communication error could also become a repair issue
                # if it's distinct from initial setup and actionable.
                raise UpdateFailed from ex

            # Process device-specific errors for actionable repair issues
            for device_mac, device_obj in self.data.items():
                if isinstance(device_obj, EheimDigitalClassicVario):
                    # --- Rotor Stuck Example ---
                    issue_id_rotor_stuck = f"rotor_stuck_{device_mac}"
                    if device_obj.error_code == FilterErrorCode.ROTOR_STUCK:
                        ir.async_create_issue(
                            self.hass,
                            DOMAIN,
                            issue_id_rotor_stuck,
                            is_fixable=False,  # User fixes externally
                            severity=ir.IssueSeverity.ERROR,
                            translation_key="rotor_stuck_repair",
                            translation_placeholders={"device_name": device_obj.name or device_mac},
                            # learn_more_url="<URL to EHEIM troubleshooting for rotor stuck>" # Optional
                        )
                    else:
                        # Clear the issue if the error is no longer present
                        ir.async_delete_issue(self.hass, DOMAIN, issue_id_rotor_stuck)

                    # --- Air in Filter Example ---
                    issue_id_air_in_filter = f"air_in_filter_{device_mac}"
                    if device_obj.error_code == FilterErrorCode.AIR_IN_FILTER:
                        ir.async_create_issue(
                            self.hass,
                            DOMAIN,
                            issue_id_air_in_filter,
                            is_fixable=False, # User fixes externally
                            severity=ir.IssueSeverity.WARNING,
                            translation_key="air_in_filter_repair",
                            translation_placeholders={"device_name": device_obj.name or device_mac},
                            # learn_more_url="<URL to EHEIM troubleshooting for air in filter>" # Optional
                        )
                    else:
                        # Clear the issue if the error is no longer present
                        ir.async_delete_issue(self.hass, DOMAIN, issue_id_air_in_filter)
                    
                    # Explicitly clear if no error is present
                    if device_obj.error_code == FilterErrorCode.NO_ERROR:
                        ir.async_delete_issue(self.hass, DOMAIN, issue_id_rotor_stuck)
                        ir.async_delete_issue(self.hass, DOMAIN, issue_id_air_in_filter)


            return self.data
    ```

3.  **Add Translations for Repair Issues:**
    In `homeassistant/components/eheimdigital/strings.json`, add new entries for the repair issues under an `issues` key:

    ```json
    {
      "config": { ... },
      "entity": { ... },
      "issues": {
        "rotor_stuck_repair": {
          "title": "{device_name}: Filter Rotor Stuck",
          "description": "The EHEIM filter '{device_name}' reports that its rotor is stuck. This can impede water flow and filtering. Please check the device for obstructions, clean the rotor, and ensure it can spin freely. Refer to the device manual for instructions. Once resolved, the issue will clear automatically."
        },
        "air_in_filter_repair": {
          "title": "{device_name}: Air in Filter System",
          "description": "The EHEIM filter '{device_name}' reports air in its system. This can reduce filter efficiency and cause noise. Please check for air leaks and bleed the filter system according to the manufacturer's instructions. Once resolved, the issue will clear automatically."
        }
        // Add other actionable error repair issues as needed
      }
    }
    ```

**Why these changes satisfy the rule:**
*   **Actionable & Informative:** The repair issues directly inform the user about a specific problem with their EHEIM device (e.g., "rotor stuck") and implicitly suggest they need to take action on the physical device.
*   **User Intervention:** These issues are raised for problems that require user intervention to fix.
*   **User-Friendly:** This mechanism is more user-friendly than relying solely on sensor states, as repair issues are prominently displayed in Home Assistant's UI, guiding the user to necessary maintenance.
*   **Clearing Issues:** The suggested code includes logic to delete the issue once the device no longer reports the error, ensuring the repair dashboard stays clean.

By implementing these changes, the `eheimdigital` integration will actively guide users to resolve actionable device problems, aligning with the `repair-issues` quality scale rule. Remember to adapt the specific `FilterErrorCode` and other device attributes based on the `eheimdigital` library's actual API.

_Created at 2025-05-27 15:43:43. Prompt tokens: 14811, Output tokens: 2015, Total tokens: 19642_
