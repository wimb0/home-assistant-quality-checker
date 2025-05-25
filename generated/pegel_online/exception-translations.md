# pegel_online: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that exceptions shown to the user that inherit from `HomeAssistantError` use translation keys defined in the integration's `strings.json` file, rather than hardcoded strings. This allows the error messages to be translated for users in different languages.

The rule applies to the `pegel_online` integration as it raises exceptions inheriting from `HomeAssistantError`.

Upon reviewing the code:

1.  In `homeassistant/components/pegel_online/__init__.py`, the `async_setup_entry` function raises `ConfigEntryNotReady` (which inherits from `HomeAssistantError`) with a hardcoded string message: `raise ConfigEntryNotReady("Failed to connect")`. This violates the rule.
2.  In `homeassistant/components/pegel_online/coordinator.py`, the `_async_update_data` function raises `UpdateFailed` (which also inherits from `HomeAssistantError`) and correctly uses `translation_domain` and `translation_key` (`"communication_error"`) which points to an entry in `strings.json`. This part follows the rule.
3.  In `homeassistant/components/pegel_online/config_flow.py`, network errors (`CONNECT_ERRORS`) and the "no stations found" condition result in showing form errors using keys (`"cannot_connect"`, `"no_stations"`) that are defined in `strings.json` under `config/error`. While not directly raising exceptions shown *after* setup, this correctly uses translated strings for user feedback during configuration.

Since the integration includes at least one instance where a hardcoded string is used with a translatable exception (`ConfigEntryNotReady` in `__init__.py`), the rule is not fully followed.

## Suggestions

To comply with the `exception-translations` rule, the `ConfigEntryNotReady` exception raised in `homeassistant/components/pegel_online/__init__.py` should use a translation key.

1.  **Add a new exception key to `strings.json`:** Add a key under the `exceptions` section for the connection failure during setup. For example:

    ```json
    {
      "config": {
        ...
      },
      "entity": {
        ...
      },
      "exceptions": {
        "communication_error": {
          "message": "Failed to communicate with API: {error}"
        },
        "setup_connection_error": { // Add this key
          "message": "Failed to connect during setup."
        }
      }
    }
    ```

2.  **Update the exception in `__init__.py`:** Modify the `raise ConfigEntryNotReady` line to use the new translation key.

    ```python
    # ...
    try:
        station = await api.async_get_station_details(station_uuid)
    except CONNECT_ERRORS as err:
        # Change this line:
        # raise ConfigEntryNotReady("Failed to connect") from err
        # To this:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="setup_connection_error",
        ) from err
    # ...
    ```

These changes ensure that the error message displayed when the integration fails to connect during initial setup is translatable, fulfilling the requirements of the rule.

_Created at 2025-05-25 11:25:16. Prompt tokens: 5947, Output tokens: 846, Total tokens: 7622_
