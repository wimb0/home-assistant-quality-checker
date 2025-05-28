```markdown
# pegel_online: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The rule `repair-issues` states that repair issues and repair flows should be used when user intervention is needed to fix a problem. It also emphasizes that issues should be actionable and informative, and not raised for problems the user cannot fix.

This rule applies to the `pegel_online` integration as it communicates with an external API and can encounter issues that might potentially require user attention (e.g., network problems).

The provided code for the `pegel_online` integration handles API communication errors (`aiopegelonline.const.CONNECT_ERRORS`) in two places:
1.  In `__init__.py`, during the initial setup when fetching station details (`api.async_get_station_details`). If a `CONNECT_ERRORS` occurs, it raises `homeassistant.exceptions.ConfigEntryNotReady` (see `homeassistant/components/pegel_online/__init__.py`, lines 31-33). This prevents the entry from being set up and is the standard way to signal an initial setup failure.
2.  In `coordinator.py`, during data updates (`api.async_get_station_measurements`). If a `CONNECT_ERRORS` occurs, it raises `homeassistant.helpers.update_coordinator.UpdateFailed` (see `homeassistant/components/pegel_online/coordinator.py`, lines 39-43). This signals a data update failure, typically causing the entity to become unavailable.

Both `ConfigEntryNotReady` and `UpdateFailed` are standard ways to handle transient or persistent communication issues within Home Assistant. However, the `pegel_online` integration does *not* utilize the `homeassistant.helpers.issue_registry` module to create repair issues for these or any other potential problems detected by the integration code.

While standard exceptions are acceptable for transient issues, persistent communication errors or other future error conditions that *do* require user action (e.g., if the API introduced authentication or changed requirements that broke existing configurations) should be communicated via repair issues according to this rule. Since the integration does not use repair issues at all, it does not fully adhere to the requirement of using them when user intervention *might* be needed, particularly for persistent problems where the user might need to check network connectivity or router settings.

Therefore, the integration is marked as **todo**.

## Suggestions

To make the integration compliant with the `repair-issues` rule, consider adding logic to create a repair issue if a communication error persists for a significant period, or if other specific error conditions arise that explicitly require user intervention.

1.  **Identify User-Actionable Scenarios:** Determine specific error cases where the user *must* do something to resolve the issue (e.g., network configuration problems leading to persistent connection failure, API requiring re-authentication in the future, specific API error codes indicating a user-fixable config issue). Based on the current code, the most likely candidate is a *persistent* connection error.
2.  **Implement Repair Issue Creation:**
    *   Modify the `PegelOnlineDataUpdateCoordinator` to track consecutive communication failures.
    *   If the number of consecutive failures exceeds a threshold (e.g., many hours or days), create a repair issue using `hass.issues.async_create_issue`.
    *   The repair issue should inform the user about the persistent communication failure and suggest potential actions (e.g., check network, check router, check API status page if applicable).
    *   Ensure the repair issue is dismissed (`hass.issues.async_delete_issue`) once a successful update occurs.
3.  **Consider Non-Fixable Issues:** If there are errors the user cannot fix but needs to be aware of (like the outdated version example in the rule), a non-fixable repair issue (`is_fixable=False`) can be used. The current `CONNECT_ERRORS` likely don't fit this, but future API changes might introduce such scenarios.
4.  **Provide Translation Strings:** Ensure translation keys are defined in `strings.json` for any new repair issues created.

**Example (Illustrative - requires careful implementation logic):**

In `coordinator.py`, add logic to track failures and create/delete issues:

```python
# In PegelOnlineDataUpdateCoordinator.__init__
self._consecutive_failures = 0

# In PegelOnlineDataUpdateCoordinator._async_update_data
async def _async_update_data(self) -> StationMeasurements:
    """Fetch data from API endpoint."""
    try:
        data = await self.api.async_get_station_measurements(self.station.uuid)
        # If successful, clear persistent error issue if it exists
        if self._consecutive_failures > 0:
             self.hass.async_create_task(
                 self.hass.issues.async_delete_issue(DOMAIN, f"persistent_communication_error_{self.station.uuid}")
             )
             self._consecutive_failures = 0
        return data
    except CONNECT_ERRORS as err:
        self._consecutive_failures += 1
        # Create a repair issue if failures are persistent
        if self._consecutive_failures > SOME_PERSISTENT_THRESHOLD: # Define a reasonable threshold
            self.hass.async_create_task(
                self.hass.issues.async_create_issue(
                    DOMAIN,
                    f"persistent_communication_error_{self.station.uuid}", # Unique issue_id per station
                    is_fixable=False, # Or True if a repair flow was implemented
                    issue_domain=DOMAIN,
                    severity=ir.IssueSeverity.ERROR, # Or WARNING
                    translation_key="persistent_communication_error", # Needs to be added to strings.json
                    translation_placeholders={"station": self.station.name, "error": str(err)},
                )
            )
        raise UpdateFailed(
            translation_domain=DOMAIN,
            translation_key="communication_error",
            translation_placeholders={"error": str(err)},
        ) from err

# Add to homeassistant/components/pegel_online/strings.json
# Under "exceptions" or a new "issues" key:
# "persistent_communication_error": {
#   "title": "Persistent communication error with {station}",
#   "description": "Home Assistant has been unable to connect to the PEGELONLINE API for station {station} for an extended period due to a communication error: {error}. Please check your internet connection and ensure the PEGELONLINE API is accessible."
# }
```

This suggestion specifically targets persistent connection errors as a potential scenario requiring user attention, aligning the integration better with the rule's requirement to use repair issues when user intervention is needed.

```

_Created at 2025-05-25 11:26:04. Prompt tokens: 5855, Output tokens: 1588, Total tokens: 11037_
