# knx: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [knx](https://www.home-assistant.io/integrations/knx/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                       |

## Overview

The `exception-translations` rule requires that error messages shown to the user, originating from exceptions inheriting `HomeAssistantError`, are translatable. This involves raising such exceptions with `translation_domain` and `translation_key` parameters, and defining the corresponding messages in the integration's `strings.json` file (typically `translations/en.json`) under a top-level `"exceptions"` key.

This rule applies to the `knx` integration as it raises exceptions (e.g., `HomeAssistantError`, `ServiceValidationError`, `ConfigEntryNotReady`) that can result in messages displayed to the user, for example, during service calls or component setup.

The `knx` integration currently does NOT fully follow this rule.
1.  **Missing `exceptions` block in `translations/en.json`**: The primary translation file (`homeassistant/components/knx/translations/en.json`) does not contain the required top-level `"exceptions": {}` structure for defining translatable exception messages.
2.  **Hardcoded error messages**: In `homeassistant/components/knx/services.py`, several instances of `HomeAssistantError` and `ServiceValidationError` (a subclass of `HomeAssistantError`) are raised with hardcoded strings or f-strings, rather than using `translation_domain` and `translation_key`.

Specific instances in `homeassistant/components/knx/services.py`:
*   In `get_knx_module()`:
    ```python
    except KeyError as err:
        raise HomeAssistantError("KNX entry not loaded") from err
    ```
    This uses a hardcoded string "KNX entry not loaded".

*   In `service_exposure_register_modify()`:
    ```python
    except KeyError as err:
        raise ServiceValidationError(
            f"Could not find exposure for '{group_address}' to remove."
        ) from err
    ```
    This uses an f-string, which is not translatable.

*   In `service_send_to_knx_bus()`:
    ```python
    if transcoder is None:
        raise ServiceValidationError(
            f"Invalid type for knx.send service: {attr_type}"
        )
    # ...
    except ConversionError as err:
        raise ServiceValidationError(
            f"Invalid payload for knx.send service: {err}"
        ) from err
    ```
    Both instances use f-strings.

Additionally, while `homeassistant/components/knx/__init__.py` raises `ConfigEntryNotReady from ex` (where `ex` is an `XKNXException`), this relies on the default message of `ConfigEntryNotReady` or the raw message from `XKNXException`. For a higher level of user experience, specific common `XKNXException` types could be caught and re-raised with specific translation keys to provide more context-aware, translatable messages for setup failures.

The `quality_scale.yaml` file for the `knx` integration also self-reports `exception-translations: todo`, aligning with this assessment.

## Suggestions

To make the `knx` integration compliant with the `exception-translations` rule, the following changes are recommended:

1.  **Modify `homeassistant/components/knx/translations/en.json`**:
    Add a top-level `"exceptions"` key. For example:
    ```json
    {
      "config": {
        // ... existing config translations ...
      },
      "exceptions": {
        "knx_entry_not_loaded": {
          "message": "KNX integration entry not loaded. Please ensure it is set up correctly."
        },
        "exposure_not_found_for_removal": {
          "message": "Could not find exposure for group address '{group_address}' to remove."
        },
        "invalid_type_for_send": {
          "message": "Invalid type '{attr_type}' specified for knx.send service."
        },
        "invalid_payload_for_send": {
          "message": "Invalid payload for knx.send service: {error}"
        }
        // Add other keys as needed
      },
      "services": {
        // ... existing service translations ...
      }
      // ... other existing translations ...
    }
    ```

2.  **Update exception raising in `homeassistant/components/knx/services.py`**:
    Modify the identified `HomeAssistantError` and `ServiceValidationError` instances to use translation keys.

    *   For `get_knx_module()`:
        ```python
        # Before
        # raise HomeAssistantError("KNX entry not loaded") from err

        # After
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="knx_entry_not_loaded",
        ) from err
        ```

    *   For `service_exposure_register_modify()`:
        ```python
        # Before
        # raise ServiceValidationError(
        #     f"Could not find exposure for '{group_address}' to remove."
        # ) from err

        # After
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="exposure_not_found_for_removal",
            translation_args={"group_address": str(group_address)},
        ) from err
        ```

    *   For `service_send_to_knx_bus()` (invalid type):
        ```python
        # Before
        # raise ServiceValidationError(
        #     f"Invalid type for knx.send service: {attr_type}"
        # )

        # After
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_type_for_send",
            translation_args={"attr_type": str(attr_type)},
        )
        ```

    *   For `service_send_to_knx_bus()` (invalid payload):
        ```python
        # Before
        # except ConversionError as err:
        #     raise ServiceValidationError(
        #         f"Invalid payload for knx.send service: {err}"
        #     ) from err

        # After
        except ConversionError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_payload_for_send",
                translation_args={"error": str(err)},
            ) from err
        ```

3.  **(Optional Enhancement) Improve `ConfigEntryNotReady` in `homeassistant/components/knx/__init__.py`**:
    For common and identifiable `XKNXException` types that occur during setup, consider catching them specifically and raising `ConfigEntryNotReady` with a dedicated `translation_key` to provide more specific and user-friendly feedback.
    Example:
    ```python
    # In async_setup_entry
    # ...
    except SpecificXknxConnectionError as ex: # Hypothetical specific exception
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="knx_connection_failed_specific",
            translation_args={"host": entry.data[CONF_HOST]} # Example argument
        ) from ex
    except XKNXException as ex:
        # Fallback for other XKNXExceptions
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="knx_setup_failed_generic",
            translation_args={"error": str(ex)}
        ) from ex
    ```
    This would require adding corresponding keys like `"knx_connection_failed_specific"` and `"knx_setup_failed_generic"` to the `"exceptions"` block in `translations/en.json`.

By implementing these changes, the `knx` integration will provide translatable error messages for exceptions, improving usability for non-English speaking users and adhering to the `exception-translations` quality scale rule.

_Created at 2025-05-14 13:37:49. Prompt tokens: 101053, Output tokens: 1871, Total tokens: 109190_
