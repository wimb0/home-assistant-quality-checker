# overkiz: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `exception-translations` rule requires that error messages shown to the user, resulting from raised exceptions inheriting from `HomeAssistantError`, are translatable. This is achieved by providing `translation_domain` and `translation_key` arguments when raising such exceptions, and defining the corresponding translations in the `strings.json` file under an `exceptions` key.

This rule applies to the `overkiz` integration. The integration raises several exceptions that are subclasses of `HomeAssistantError` (e.g., `ConfigEntryAuthFailed`, `ConfigEntryNotReady`, `UpdateFailed`, `HomeAssistantError`) during its setup and runtime operations. Currently, these exceptions are raised with hardcoded English strings, and the `strings.json` file does not contain the required `exceptions` block for these translations.

**Code Analysis:**

1.  **`homeassistant/components/overkiz/__init__.py` (`async_setup_entry` function):**
    *   `raise ConfigEntryAuthFailed("Invalid authentication") from exception`
    *   `raise ConfigEntryNotReady("Too many requests, try again later") from exception`
    *   `raise ConfigEntryNotReady("Failed to connect") from exception`
    *   `raise ConfigEntryNotReady("Server is down for maintenance") from exception`
    These exceptions are subclasses of `HomeAssistantError` but are raised with hardcoded strings instead of `translation_domain` and `translation_key`.

2.  **`homeassistant/components/overkiz/coordinator.py` (`OverkizDataUpdateCoordinator._async_update_data` function):**
    *   `raise ConfigEntryAuthFailed("Invalid authentication.") from exception`
    *   `raise UpdateFailed("Too many concurrent requests.") from exception`
    *   `raise UpdateFailed("Too many requests, try again later.") from exception`
    *   `raise UpdateFailed("Server is down for maintenance.") from exception`
    *   `raise UpdateFailed(exception) from exception` (for `InvalidEventListenerIdException` - message is from the library)
    *   `raise UpdateFailed("Failed to connect.") from exception`
    *   In the relogin block:
        *   `raise ConfigEntryAuthFailed("Invalid authentication.") from exception`
        *   `raise UpdateFailed("Too many requests, try again later.") from exception`
    Similar to `__init__.py`, these `HomeAssistantError` subclasses are raised with hardcoded strings or library messages.

3.  **`homeassistant/components/overkiz/executor.py` (`OverkizExecutor.async_execute_command` function):**
    *   `raise HomeAssistantError(exception) from exception`
    This re-raises a `BaseOverkizException` (from the `pyoverkiz` library) as a `HomeAssistantError`. The message is taken directly from the library exception, which is not translatable by Home Assistant's mechanism and may not be user-friendly.

4.  **`homeassistant/components/overkiz/strings.json`:**
    *   The file contains translations for config flow (`config.error`, `config.abort`) and entity states/attributes (`entity.*`).
    *   However, it is missing the `exceptions: {}` block required by this rule for translating messages from `HomeAssistantError` and its subclasses.

While the config flow (`config_flow.py`) uses `errors["base"] = "error_key"` with corresponding translations in `strings.json` under `config.error`, this mechanism is specific to config flow UI error reporting. The `exception-translations` rule specifically targets exceptions derived from `HomeAssistantError` that are raised and then handled by Home Assistant's core error display mechanisms (e.g., during setup, service calls, entity updates).

The integration does not currently follow the rule as it uses hardcoded strings for `HomeAssistantError` subclasses and lacks the necessary `exceptions` section in `strings.json`.

## Suggestions

To make the `overkiz` integration compliant with the `exception-translations` rule, the following changes are recommended:

1.  **Add an `exceptions` block to `homeassistant/components/overkiz/strings.json`:**
    Create a new top-level key `exceptions` in `strings.json` and add translation keys for each distinct error message.

    Example structure for `strings.json`:
    ```json
    {
      "config": {
        // ... existing config flow translations ...
      },
      "exceptions": {
        "invalid_auth": {
          "message": "Invalid authentication credentials."
        },
        "too_many_requests_setup": {
          "message": "Setup failed due to too many requests. Please try again later."
        },
        "connect_failed_setup": {
          "message": "Failed to connect to the Overkiz hub/service during setup."
        },
        "maintenance_setup": {
          "message": "The Overkiz service is down for maintenance. Setup cannot proceed at this time."
        },
        "update_failed_too_many_concurrent": {
          "message": "Update failed: Too many concurrent requests to the Overkiz service."
        },
        "update_failed_too_many_requests": {
          "message": "Update failed: Too many requests to the Overkiz service. Please try again later."
        },
        "update_failed_maintenance": {
          "message": "Update failed: The Overkiz service is down for maintenance."
        },
        "update_failed_listener_invalid": {
          "message": "Data update failed: The event listener is invalid. Details: {error}"
        },
        "update_failed_connect": {
          "message": "Data update failed: Could not connect to the Overkiz service."
        },
        "command_failed": {
          "message": "Failed to execute command: {error}"
        }
        // Add other specific keys as identified
      },
      "entity": {
        // ... existing entity translations ...
      }
    }
    ```

2.  **Update `raise` statements to use translation keys:**
    Modify the Python code where `HomeAssistantError` (or its subclasses like `ConfigEntryAuthFailed`, `ConfigEntryNotReady`, `UpdateFailed`) are raised.

    **In `homeassistant/components/overkiz/__init__.py`:**
    Replace lines like:
    `raise ConfigEntryAuthFailed("Invalid authentication") from exception`
    With:
    ```python
    from .const import DOMAIN # Ensure DOMAIN is imported

    # ...
    raise ConfigEntryAuthFailed(
        translation_domain=DOMAIN,
        translation_key="invalid_auth"
    ) from exception
    ```
    Do this for all relevant `raise` statements (e.g., `ConfigEntryNotReady` for "too_many_requests_setup", "connect_failed_setup", "maintenance_setup").

    **In `homeassistant/components/overkiz/coordinator.py`:**
    Similarly, update `raise` statements. For example:
    `raise UpdateFailed("Too many concurrent requests.") from exception`
    Becomes:
    ```python
    from .const import DOMAIN # Ensure DOMAIN is imported

    # ...
    raise UpdateFailed(
        translation_domain=DOMAIN,
        translation_key="update_failed_too_many_concurrent"
    ) from exception
    ```
    For `raise UpdateFailed(exception) from exception` where `exception` is `InvalidEventListenerIdException`:
    ```python
    raise UpdateFailed(
        translation_domain=DOMAIN,
        translation_key="update_failed_listener_invalid",
        translation_placeholders={"error": str(exception)}
    ) from exception
    ```

    **In `homeassistant/components/overkiz/executor.py`:**
    For `raise HomeAssistantError(exception) from exception`:
    ```python
    from .const import DOMAIN # Ensure DOMAIN is imported
    from pyoverkiz.exceptions import BaseOverkizException # Already imported

    # ...
    except BaseOverkizException as py_ex:
        # Consider mapping specific pyoverkiz exceptions to more specific translation keys if appropriate.
        # For a general case:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="command_failed",
            translation_placeholders={"error": str(py_ex)}
        ) from py_ex
    ```

**Why these changes satisfy the rule:**

*   Raising exceptions with `translation_domain` and `translation_key` allows Home Assistant's core to look up the appropriate translated string from the integration's `strings.json` file.
*   Defining these strings under the `exceptions` key in `strings.json` provides the source for these translations.
*   This approach ensures that users see localized error messages, improving usability for non-English speakers. It also decouples the error messages from the Python code, making them easier to manage and update.

_Created at 2025-05-28 12:40:14. Prompt tokens: 87051, Output tokens: 2129, Total tokens: 93722_
