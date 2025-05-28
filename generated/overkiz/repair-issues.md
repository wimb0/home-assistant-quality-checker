# overkiz: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `repair-issues` rule requires integrations to use repair issues and repair flows to inform users when something is wrong and user intervention is needed. These notifications should be actionable and informative.

The `overkiz` integration interacts with external cloud services or local Overkiz-compatible hubs. This makes it susceptible to issues like authentication failures, API rate limits, server maintenance, or changes in device/API compatibility, many of which could benefit from the repair issue system for better user feedback.

Currently, the `overkiz` integration handles some of these situations:
*   **Authentication failures** (e.g., `BadCredentialsException`, `NotSuchTokenException`): It raises `ConfigEntryAuthFailed` in both `async_setup_entry` (`__init__.py`) and `OverkizDataUpdateCoordinator._async_update_data` (`coordinator.py`). This correctly triggers Home Assistant's built-in re-authentication flow, which is a type of repair flow.
*   **Service unavailability during setup** (e.g., `TooManyRequestsException`, `MaintenanceException` in `async_setup_entry`): It raises `ConfigEntryNotReady`. Home Assistant will retry setting up the entry, but no specific repair issue is created to inform the user about the cause of the delay.
*   **Service unavailability during runtime** (e.g., `TooManyRequestsException`, `MaintenanceException`, `TooManyConcurrentRequestsException` in `coordinator._async_update_data`): It raises `UpdateFailed`. The coordinator logs an error and retries, but no repair issue is created.
*   **`InvalidEventListenerIdException` during runtime**: It raises `UpdateFailed`. If this issue is persistent, retries may not resolve it, and the user isn't guided towards a potential fix (like reloading the integration).

While the use of `ConfigEntryAuthFailed` addresses authentication issues with a repair flow, the integration does not utilize `homeassistant.helpers.issue_registry.async_create_issue` to explicitly create repair issues for other scenarios where user awareness or action could be beneficial, or to provide a more guided fix for specific non-auth persistent errors. The rule's example demonstrates creating an issue registry entry even when just informing the user about an externally fixable problem (`is_fixable=False`).

Therefore, the integration does not fully follow the `repair-issues` rule as it misses opportunities to create repair *issues* for several relevant scenarios.

## Suggestions

To comply with the `repair-issues` rule, the `overkiz` integration should implement `homeassistant.helpers.issue_registry` for specific error conditions.

**1. Import necessary modules:**
```python
# In __init__.py and coordinator.py
import homeassistant.helpers.issue_registry as ir
from homeassistant.exceptions import ConfigEntryError # If not already imported
# For repair flows if needed:
# from homeassistant.helpers.issue_registry import RepairsFlow
```

**2. Handle setup-time `MaintenanceException` and `TooManyRequestsException` in `__init__.py`:**
These currently raise `ConfigEntryNotReady`. An issue can inform the user about the delay.

```python
# In __init__.py, within async_setup_entry's try-except block:

# ...
except TooManyRequestsException as exception:
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"setup_too_many_requests_{entry.entry_id}", # Unique issue ID per entry
        is_fixable=False,
        translation_key="setup_too_many_requests",
        translation_placeholders={"server": client.server.name if client else entry.data.get(CONF_HUB)},
        severity=ir.IssueSeverity.WARNING,
    )
    raise ConfigEntryNotReady("Too many requests, try again later") from exception
except MaintenanceException as exception:
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"setup_server_maintenance_{entry.entry_id}", # Unique issue ID per entry
        is_fixable=False,
        translation_key="setup_server_maintenance",
        translation_placeholders={"server": client.server.name if client else entry.data.get(CONF_HUB)},
        severity=ir.IssueSeverity.WARNING,
    )
    raise ConfigEntryNotReady("Server is down for maintenance") from exception
# ...

# At the end of successful setup in async_setup_entry:
ir.async_delete_issue(hass, DOMAIN, f"setup_too_many_requests_{entry.entry_id}")
ir.async_delete_issue(hass, DOMAIN, f"setup_server_maintenance_{entry.entry_id}")
```
*Why:* This makes the user aware of why the integration might be taking longer to set up. The issues are cleared upon successful setup. The issue ID should be unique, for example, by including the `config_entry.entry_id`.

**3. Handle persistent runtime `InvalidEventListenerIdException` in `coordinator.py`:**
This error might require a manual reload of the integration. A repair issue with a fix flow can guide the user.

```python
# In coordinator.py, within OverkizDataUpdateCoordinator._async_update_data:

# ...
except InvalidEventListenerIdException as exception:
    # Consider adding logic to only create the issue if it persists after a few retries
    ir.async_create_issue(
        self.hass,
        DOMAIN,
        f"invalid_event_listener_{self.config_entry.entry_id}",
        is_fixable=True, # This requires a repair flow
        data={"entry_id": self.config_entry.entry_id},
        translation_key="invalid_event_listener",
        learn_more_url="<URL to documentation explaining potential causes or steps if any>",
        severity=ir.IssueSeverity.ERROR,
        # break_config_entry=True # This could be used to stop further updates until fixed
    )
    raise UpdateFailed(exception) from exception
# ...

# In __init__.py (or a new repairs.py):
# You would need to register a repair flow for "invalid_event_listener"
# Example (simplified):
# async def async_create_invalid_event_listener_fix_flow(hass, issue_id, data):
#     class FixFlow(ir.RepairsFlow):
#         async def async_step_init(self, user_input=None):
#             return self.async_show_form(step_id="confirm_reload", 
#                                         description_placeholders={"entry_title": self.hass.config_entries.async_get_entry(data["entry_id"]).title})
#
#         async def async_step_confirm_reload(self, user_input=None):
#             entry_id = data["entry_id"]
#             self.hass.async_create_task(self.hass.config_entries.async_reload(entry_id))
#             ir.async_delete_issue(self.hass, DOMAIN, issue_id)
#             return self.async_create_entry(title="", data={})
#     return FixFlow()
#
# async def async_setup_entry(...):
#   ...
#   if not hass.data.get(DOMAIN, {}).get("repairs_registered"): # Ensure one-time registration
#       ir.async_register_repair_flow(
#           hass,
#           DOMAIN,
#           lambda issue_id, data: issue_id.startswith("invalid_event_listener_"), # Check if issue_id matches pattern
#           async_create_invalid_event_listener_fix_flow,
#       )
#       hass.data.setdefault(DOMAIN, {})["repairs_registered"] = True
#   ...
#
# When the coordinator successfully fetches events after this issue:
# ir.async_delete_issue(self.hass, DOMAIN, f"invalid_event_listener_{self.config_entry.entry_id}")
```
*Why:* This provides a user-actionable fix ("Reload Integration") directly from the Repairs dashboard if the event listener becomes permanently invalid. `is_fixable=True` allows HA to show a "FIX ISSUE" button. The repair flow is triggered by `issue_id`, so make sure it's unique but identifiable.

**4. Handle persistent runtime `MaintenanceException` / `TooManyRequestsException` in `coordinator.py`:**
If these errors occur repeatedly during updates, an informational issue can be helpful.

```python
# In OverkizDataUpdateCoordinator:
# Add attributes to track persistent errors, e.g., self._maintenance_errors_count = 0

# In _async_update_data, within the except block for MaintenanceException:
# ...
# except MaintenanceException as exception:
#     self._maintenance_errors_count += 1
#     if self._maintenance_errors_count >= 3: # Threshold for creating an issue
#         ir.async_create_issue(
#             self.hass,
#             DOMAIN,
#             f"update_server_maintenance_{self.config_entry.entry_id}",
#             is_fixable=False,
#             translation_key="update_server_maintenance",
#             translation_placeholders={"server": self.client.server.name},
#             severity=ir.IssueSeverity.WARNING,
#         )
#     raise UpdateFailed("Server is down for maintenance.") from exception

# On successful update (e.g., at the end of _async_update_data after successful events fetch):
# if self._maintenance_errors_count > 0: # Or if the specific issue exists
#     ir.async_delete_issue(self.hass, DOMAIN, f"update_server_maintenance_{self.config_entry.entry_id}")
#     self._maintenance_errors_count = 0
# (Similar logic for TooManyRequestsException)
```
*Why:* Informs the user if the integration is consistently failing to update due to external service issues, rather than silently retrying. The issue is cleared when the service recovers.

**5. Authentication Issues (`BadCredentialsException`, etc.):**
The current use of `ConfigEntryAuthFailed` triggers a reauth flow, which is good. If the goal is merely to have an explicit entry in the Repairs dashboard for these, you could add:
```python
# Example for BadCredentialsException in async_setup_entry:
except BadCredentialsException as exception:
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"auth_failed_{entry.entry_id}",
        is_fixable=False, # Reauth is handled by ConfigEntryAuthFailed
        translation_key="auth_failed_reconfigure",
        translation_placeholders={"server": client.server.name if client else entry.data.get(CONF_HUB)},
        severity=ir.IssueSeverity.ERROR,
    )
    raise ConfigEntryAuthFailed("Invalid authentication") from exception

# On successful reauth (Home Assistant might clear this automatically if tied to entry state, or manual clearing via config entry update listener might be needed)
```
*Why:* This would list the auth failure in the Repairs dashboard alongside the reconfigure prompt from `ConfigEntryAuthFailed`. `is_fixable=False` is suggested here to avoid interfering with the standard reauth flow that `ConfigEntryAuthFailed` triggers, with the issue text guiding the user to the reauth prompt.

**6. Add Translations:**
Add the new `translation_key`s (e.g., `setup_too_many_requests`, `setup_server_maintenance`, `update_server_maintenance`, `invalid_event_listener`, `auth_failed_reconfigure`) to `strings.json` with informative messages for the user. For fixable issues, also provide translations for the repair flow steps.

By implementing these suggestions, the `overkiz` integration will provide more robust and user-friendly error reporting, aligning with the `repair-issues` quality scale rule.

_Created at 2025-05-28 12:45:55. Prompt tokens: 86959, Output tokens: 2815, Total tokens: 98036_
