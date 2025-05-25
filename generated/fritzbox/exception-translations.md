```markdown
# fritzbox: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that user-facing error messages raised via exceptions are translatable using `HomeAssistantError` or its subclasses with `translation_domain` and `translation_key`, defined in the `exceptions` section of the integration's `strings.json` file. The rule applies to all integrations.

The `fritzbox` integration partially follows this rule:

1.  The `config_flow.py` handles errors (`LoginError`, `RequestConnectionError`, `HTTPError`) during the configuration flow by returning specific `ConfigFlowResult` values (e.g., `RESULT_INVALID_AUTH`, `RESULT_NO_DEVICES_FOUND`, `RESULT_NOT_SUPPORTED`). These results map to messages defined in the `config.flow.abort` and `config.flow.error` sections of `strings.json`, which is the standard and correct way to handle translatable errors during the config flow steps.
2.  The `switch.py` and `climate.py` files correctly raise `HomeAssistantError` with `translation_domain=DOMAIN` and specific `translation_key` values (e.g., `manual_switching_disabled`, `change_settings_while_active_mode`, `change_settings_while_lock_enabled`) when specific conditions are met. These keys exist in the `exceptions` section of the `strings.json` file. This correctly implements the rule for runtime entity errors.
3.  However, the `coordinator.py` file raises `HomeAssistantError` subclasses (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `UpdateFailed`) during setup (`async_setup`) and update (`_update_fritz_devices`) without providing the `translation_domain` and `translation_key` arguments. These exceptions represent user-facing errors (e.g., shown on the integration tile for setup failures, or in logs/notifications for update failures). Although `HomeAssistantError` subclasses are used, omitting the translation arguments means the resulting user messages might not be properly translatable, or rely on default untranslated messages.

Specifically:

*   In `coordinator.py`, `async_setup`:
    ```python
    except RequestConnectionError as err:
        raise ConfigEntryNotReady from err # Missing translation_domain, translation_key
    except LoginError as err:
        raise ConfigEntryAuthFailed from err # Missing translation_domain, translation_key
    ```
*   In `coordinator.py`, `_update_fritz_devices`:
    ```python
    except RequestConnectionError as ex:
        raise UpdateFailed from ex # Missing translation_domain, translation_key
    except HTTPError:
        # ... re-login attempt ...
        except LoginError as ex:
            raise ConfigEntryAuthFailed from ex # Missing translation_domain, translation_key
    ```

To fully comply with the rule, these exceptions should be raised with explicit translation keys defined in `strings.json`.

## Suggestions

To make the integration fully compliant with the `exception-translations` rule, update the `coordinator.py` file to raise `HomeAssistantError` subclasses with `translation_domain` and `translation_key`, and add the corresponding messages to the `exceptions` section in `strings.json`.

1.  **Update `homeassistant/components/fritzbox/coordinator.py`**: Modify the exception raising points to include the translation arguments.

    ```python
    from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady, HomeAssistantError, UpdateFailed
    # ... other imports ...
    from .const import DOMAIN, LOGGER

    # ... inside async_setup ...
    try:
        await self.hass.async_add_executor_job(self.fritz.login)
    except RequestConnectionError as err:
        # Add translation keys
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="connection_error_setup"
        ) from err
    except LoginError as err:
        # Add translation keys
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN, translation_key="login_error"
        ) from err

    # ... inside _update_fritz_devices ...
    def _update_fritz_devices(self) -> FritzboxCoordinatorData:
        """Update all fritzbox device data."""
        try:
            self.fritz.update_devices(ignore_removed=False)
            if self.has_templates:
                self.fritz.update_templates(ignore_removed=False)
        except RequestConnectionError as ex:
            # Add translation keys
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="connection_error_update"
            ) from ex
        except HTTPError:
            # If the device rebooted, login again
            try:
                self.fritz.login()
            except LoginError as ex:
                # Add translation keys (can reuse login_error key)
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN, translation_key="login_error"
                ) from ex
            # ... rest of HTTPError handling ...
    ```

2.  **Update `homeassistant/components/fritzbox/strings.json`**: Add the new translation keys to the `exceptions` section.

    ```json
    {
      "config": { ... },
      "entity": { ... },
      "exceptions": {
        "manual_switching_disabled": {
          "message": "Can't toggle switch while manual switching is disabled for the device."
        },
        "change_settings_while_lock_enabled": {
          "message": "Can't change settings while manual access for telephone, app, or user interface is disabled on the device"
        },
        "change_settings_while_active_mode": {
          "message": "Can't change settings while holiday or summer mode is active on the device."
        },
        "connection_error_setup": {
          "message": "Could not connect to FRITZ!Box during setup."
        },
        "connection_error_update": {
          "message": "Could not connect to FRITZ!Box during update."
        },
        "login_error": {
          "message": "Login failed. Check your username and password."
        }
      }
    }
    ```

These changes ensure that key connection and authentication errors reported to the user originating from the coordinator are also translatable, fully adhering to the rule.

```

_Created at 2025-05-25 11:37:17. Prompt tokens: 19042, Output tokens: 1547, Total tokens: 22688_
