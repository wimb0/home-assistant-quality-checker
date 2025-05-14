# knx: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [knx](https://www.home-assistant.io/integrations/knx/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `repair-issues` rule requires integrations to use repair issues and repair flows when user intervention is needed to fix a problem. These should be actionable and informative.

The KNX integration currently does not fully follow this rule.
While the `config_flow.py` handles errors during the initial setup or options flow by presenting form errors to the user, problems that arise *after* setup (e.g., on Home Assistant startup or during runtime) due to user-fixable configuration issues are not consistently creating repair issues.

Specifically, in `homeassistant/components/knx/__init__.py`, the `async_setup_entry` function catches general `XKNXException`s during the startup of the KNX connection (`await knx_module.start()`) and raises `ConfigEntryNotReady`:
```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # ...
    try:
        knx_module = KNXModule(hass, config, entry)
        await knx_module.start()
    except XKNXException as ex:
        raise ConfigEntryNotReady from ex # <--- Generic handling
    # ...
```
Some subtypes of `XKNXException` indicate user-fixable problems, such as:
*   `knx.exceptions.InvalidSecureConfiguration`: This can occur if a KNX keyring file (`.knxkeys`) password stored in the config entry is incorrect, or if the keyring file itself (referenced by the config entry and stored by Home Assistant) becomes corrupted or is missing. The user would need to update the password or re-upload the keyring file via the integration's options flow.
*   Persistent `knx.exceptions.CommunicationError` (or its subtypes like `knx.io.KNXIPInterfaceError`): If these errors are due to incorrect stored configuration (e.g., wrong IP address, port for a tunneling connection that was previously working or was manually entered incorrectly and saved), the user needs to correct this via the options flow.

In these cases, simply raising `ConfigEntryNotReady` doesn't provide the user with actionable information or a clear path to resolution as mandated by the `repair-issues` rule. Instead, a repair issue should be created to inform the user about the specific problem and guide them (e.g., to the options flow).

The integration's `quality_scale.yaml` also indicates `repair-issues: todo`, confirming this area needs implementation.

## Suggestions

To make the `knx` integration compliant with the `repair-issues` rule, the following changes are recommended:

1.  **Refine Exception Handling in `async_setup_entry`**:
    Instead of a generic `except XKNXException`, catch specific, user-fixable exception types first.

2.  **Create Repair Issues for User-Fixable Problems**:
    For these specific exceptions, use `homeassistant.helpers.issue_registry.async_create_issue` to create a repair issue.
    *   Set `is_fixable=False` as the user typically needs to use the options flow or perform external actions (like fixing a network issue or turning on an interface). Home Assistant itself cannot automatically fix these.
    *   Use appropriate `severity`, `translation_key` (to provide a user-friendly message from `strings.json`), and `learn_more_url` pointing to relevant documentation.
    *   Raise `ConfigEntryError` instead of `ConfigEntryNotReady` for these permanent, user-fixable configuration errors, as `ConfigEntryNotReady` is typically for transient issues.

3.  **Add Translation Strings**:
    Add the necessary translation strings for the repair issues in `strings.json` to explain the problem and suggest solutions.

**Example Code Modification in `homeassistant/components/knx/__init__.py`:**

```python
# Add necessary imports
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import issue_registry as ir
from xknx.exceptions import InvalidSecureConfiguration, CommunicationError # and other relevant XKNXException subtypes

# ... inside async_setup_entry ...
    # ...
    try:
        knx_module = KNXModule(hass, config, entry)
        await knx_module.start()
    except InvalidSecureConfiguration as ex:
        # Example for invalid KNX secure configuration (e.g., bad knxkeys password)
        issue_id = "invalid_knx_secure_config"
        translation_key = "knx_secure_config_error"
        # Check if an issue for this specific problem already exists to avoid spamming
        # This might require more sophisticated issue management if errors are frequent
        # For startup errors, this is usually fine.
        if not ir.async_issue_exists(hass, DOMAIN, issue_id):
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False, # User needs to go to Options Flow
                severity=ir.IssueSeverity.ERROR,
                translation_key=translation_key,
                translation_placeholders={"error_message": str(ex)},
                learn_more_url="https://www.home-assistant.io/integrations/knx/#knx-ip-secure" # Example URL
            )
        # For permanent configuration errors, ConfigEntryError is more appropriate
        raise ConfigEntryError(f"KNX Secure configuration error: {ex}") from ex
    except CommunicationError as ex:
        # This needs careful consideration to distinguish persistent config-related
        # communication errors from transient network issues.
        # A simple approach might be to create an issue if it occurs during startup.
        # For a more robust solution, one might only raise this if, e.g., it's a KNXIPInterfaceError
        # clearly pointing to a bad host/port from entry.data.
        issue_id = "knx_connection_issue"
        translation_key = "knx_connection_error_check_config"
        if not ir.async_issue_exists(hass, DOMAIN, issue_id):
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key=translation_key,
                translation_placeholders={"error_message": str(ex)},
                learn_more_url="https://www.home-assistant.io/integrations/knx/#connectivity-issues" # Example URL
            )
        raise ConfigEntryError(f"KNX connection error: {ex}") from ex
    except XKNXException as ex:
        # Fallback for other XKNX exceptions
        _LOGGER.error("Error setting up KNX: %s", ex)
        # ConfigEntryNotReady might be appropriate if it's potentially transient
        # or not clearly user-fixable through config.
        raise ConfigEntryNotReady(f"KNX initialization failed: {ex}") from ex
    # ...
```

**Corresponding `strings.json` additions (example):**
```json
{
  "issues": {
    "invalid_knx_secure_config": {
      "title": "KNX Secure Configuration Error",
      "description": "There is an issue with your KNX IP Secure configuration: `{error_message}`.\n\nPlease check your KNX keyring file and password in the KNX integration options. You may need to re-upload your `.knxkeys` file or update the password."
    },
    "knx_connection_error_check_config": {
      "title": "KNX Connection Error",
      "description": "Failed to connect to the KNX interface: `{error_message}`.\n\nPlease verify your connection settings (e.g., IP address, port, connection type) in the KNX integration options. Ensure your KNX IP interface is powered on and accessible on the network."
    }
    // Add other repair issue strings as needed
  }
}
```

By implementing these suggestions, the KNX integration will provide more user-friendly and actionable feedback when configuration-related issues prevent it from starting correctly, thereby adhering to the `repair-issues` quality scale rule.

_Created at 2025-05-14 11:40:00. Prompt tokens: 100961, Output tokens: 1954, Total tokens: 107920_
