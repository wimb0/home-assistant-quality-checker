# open_epaper_link: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |

## Overview

The `exception-translations` rule requires that user-facing error messages, particularly those derived from `HomeAssistantError` or its subclasses, are translatable. This ensures a better user experience for non-English speaking users.

This rule applies to the `open_epaper_link` integration because it:
1.  Raises `HomeAssistantError` exceptions in its service handlers (`services.py`) with messages intended for the user.
2.  Presents error messages to the user during the configuration flow (`config_flow.py`).

The integration currently does **not** follow this rule for the following reasons:

1.  **Untranslatable `HomeAssistantError` exceptions in services:**
    In `homeassistant/components/open_epaper_link/services.py`, `HomeAssistantError` exceptions are raised with hardcoded f-strings. These messages are not translatable as they do not use the `translation_domain` and `translation_key` parameters.
    For example:
    *   In `get_entity_id_from_device_id`:
        ```python
        if not device:
            raise HomeAssistantError(f"Device {device_id} not found")
        # ...
        if domain_mac[0] != DOMAIN:
            raise HomeAssistantError(f"Device {device_id} is not an OpenEPaperLink device")
        ```
    *   In `get_hub`:
        ```python
        if DOMAIN not in hass.data or not hass.data[DOMAIN]:
            raise HomeAssistantError("Integration not configured")
        ```
    *   In `drawcustom_service`:
        ```python
        if not hub.online:
            raise HomeAssistantError(
                "AP is offline. Please check your network connection and AP status."
            )
        # ...
        if errors:
            raise HomeAssistantError("\n".join(errors)) # 'errors' contains f-strings
        ```
    *   In `upload_image`:
        ```python
        raise HomeAssistantError(
            f"Image upload failed for {entity_id} with status code: {response.status_code}"
        )
        ```
    *   In `deprecated_service_handler`:
        ```python
        raise HomeAssistantError(
            f"The service {DOMAIN}.{old_service} has been removed. "
            f"Please use {DOMAIN}.drawcustom instead. "
            "See the documentation for more details."
        )
        ```

2.  **Missing translations for config flow errors:**
    In `homeassistant/components/open_epaper_link/config_flow.py`, error messages are set using keys like `errors["base"] = "cannot_connect"`, `errors["base"] = "timeout"`, and `errors["base"] = "unknown"`. For these messages to be translatable by the integration, corresponding entries must exist in the `strings.json` file under the `config.error` section.
    The current `homeassistant/components/open_epaper_link/strings.json` file is:
    ```json
    {
      "config": {
        "step": {
          "user": {
            "data": {
              "host": "[%key:common::config_flow::data::host%]"
            }
          }
        }
      }
    }
    ```
    This file lacks the necessary `config.error` definitions for `cannot_connect`, `timeout`, and `unknown`.

3.  **`strings.json` lacks an `exceptions` block:**
    To translate `HomeAssistantError` exceptions, their translation keys must be defined in an `exceptions` block within the `strings.json` file. This block is currently missing.

## Suggestions

To make the `open_epaper_link` integration compliant with the `exception-translations` rule, the following changes are recommended:

1.  **Modify `HomeAssistantError` calls in `services.py`:**
    Update all instances where `HomeAssistantError` is raised with hardcoded messages to use `translation_domain` and `translation_key`. Placeholders can be passed via `translation_placeholders`.

    *   **Example current code (in `services.py` -> `get_entity_id_from_device_id`):**
        ```python
        if not device:
            raise HomeAssistantError(f"Device {device_id} not found")
        ```

    *   **Suggested change:**
        ```python
        from .const import DOMAIN # Ensure DOMAIN is imported

        # ...
        if not device:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="device_not_found",
                translation_placeholders={"device_id": device_id},
            )
        ```
    Repeat this pattern for all user-facing `HomeAssistantError` exceptions in `services.py`.

2.  **Add an `exceptions` block to `strings.json`:**
    Create an `exceptions` section in `homeassistant/components/open_epaper_link/strings.json` to define the translatable messages for the keys used in `services.py`.

    *   **Example `strings.json` addition:**
        ```json
        {
          "config": {
            // ... existing config section ...
          },
          "exceptions": {
            "device_not_found": {
              "message": "Device '{device_id}' not found."
            },
            "no_identifiers_for_device": {
              "message": "No identifiers found for device '{device_id}'."
            },
            "not_an_open_epaper_link_device": {
              "message": "Device '{device_id}' is not an OpenEPaperLink device."
            },
            "integration_not_configured": {
              "message": "The OpenEPaperLink integration is not configured."
            },
            "ap_offline": {
              "message": "The OpenEPaperLink AP is offline. Please check its network connection and status."
            },
            "drawcustom_processing_error": {
              "message": "Error processing drawcustom for device {entity_id}: {error_message}"
            },
            "drawcustom_failed_to_process_device": {
              "message": "Failed to process drawcustom for device {device_id}: {error_message}"
            },
            "drawcustom_errors_occurred": {
              "message": "One or more errors occurred during the drawcustom service: {error_details}"
            },
            "image_upload_failed_status": {
              "message": "Image upload failed for {entity_id} with status code: {status_code}."
            },
            "image_upload_timeout": {
              "message": "Image upload timed out for {entity_id}."
            },
            "image_upload_failed_exception": {
              "message": "Failed to upload image for {entity_id}: {error_message}."
            },
            "deprecated_service": {
              "message": "The service 'open_epaper_link.{old_service}' has been removed. Please use 'open_epaper_link.drawcustom' instead. See the documentation for more details."
            }
            // ... add other keys as needed
          }
        }
        ```

3.  **Add `config.error` keys to `strings.json` for `config_flow.py`:**
    Define the error keys used in `config_flow.py` (e.g., `cannot_connect`, `timeout`, `unknown`) within the `config.error` section of `strings.json`.

    *   **Example `strings.json` addition:**
        ```json
        {
          "config": {
            "step": {
              "user": {
                "data": {
                  "host": "[%key:common::config_flow::data::host%]"
                }
              }
            },
            "error": {
              "cannot_connect": "Failed to connect to the OpenEPaperLink AP. Please check the host address and ensure the AP is reachable.",
              "timeout": "Connection to the OpenEPaperLink AP timed out. Please ensure it is online and responsive.",
              "unknown": "An unknown error occurred while attempting to connect to the OpenEPaperLink AP. Check logs for more details."
            },
            "abort": {
              // If you have abort reasons, define them here
            }
          },
          "exceptions": {
            // ... as defined above ...
          }
        }
        ```

By implementing these suggestions, the error messages presented to the user by the `open_epaper_link` integration will become translatable, aligning with the `exception-translations` rule and improving the experience for international users.

_Created at 2025-05-14 21:04:21. Prompt tokens: 60540, Output tokens: 2105, Total tokens: 69245_
