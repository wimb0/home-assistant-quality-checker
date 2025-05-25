```markdown
# fritzbox: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `repair-issues` rule requires integrations to use repair issues and repair flows for problems that require user intervention and are fixable by the user. These mechanisms should be actionable and informative.

This rule applies to the `fritzbox` integration as it connects to an external device and may encounter issues like connectivity problems or authentication failures that a user can resolve.

The integration handles potential connection and authentication failures in its `FritzboxDataUpdateCoordinator` (`homeassistant/components/fritzbox/coordinator.py`). Specifically:

1.  During the initial setup in `async_setup`, if `pyfritzhome.login()` fails due to `LoginError`, a `ConfigEntryAuthFailed` exception is raised. If it fails due to `RequestConnectionError`, a `ConfigEntryNotReady` exception is raised.
2.  During updates in `_update_fritz_devices`, if `pyfritzhome.update_devices()` or `pyfritzhome.update_templates()` fail due to `RequestConnectionError`, an `UpdateFailed` exception is raised. If an `HTTPError` occurs, the integration attempts to log in again, and if that fails with `LoginError`, a `ConfigEntryAuthFailed` is raised.

Raising `ConfigEntryAuthFailed` in the coordinator is the standard and recommended way for an integration to signal an authentication issue that requires user intervention. Home Assistant's core automatically detects this exception and triggers a reauthentication flow for the affected config entry. This reauthentication flow is presented to the user in the Home Assistant UI's Repairs dashboard, guiding them through re-entering credentials. This process leverages the built-in repair flow mechanism provided by Home Assistant core.

While the integration does not explicitly call `ir.async_create_issue` to create a custom repair issue, it correctly utilizes the `ConfigEntryAuthFailed` exception, which implicitly triggers a core-managed repair flow for the most critical user-fixable problem: authentication failure.

Other potential issues handled by the integration, such as connection errors (`ConfigEntryNotReady`, `UpdateFailed`) typically result in the entities becoming unavailable, which is a clear indication to the user without needing a separate repair issue. Runtime errors on entities due to device states (like locks or modes in `climate.py` and `switch.py`) are raised as `HomeAssistantError` during service calls, which is appropriate for immediate feedback rather than a persistent repair issue.

Based on this analysis, the integration effectively uses the core Home Assistant repair mechanism for authentication errors, which is a key actionable problem for the user. It handles other errors appropriately using standard HA practices. Therefore, the integration follows the requirements of the `repair-issues` rule for the types of issues it encounters.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:37:53. Prompt tokens: 18950, Output tokens: 701, Total tokens: 21699_
