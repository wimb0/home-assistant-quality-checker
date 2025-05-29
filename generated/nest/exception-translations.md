# nest: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `exception-translations` rule requires that exception messages intended for the user are translatable. This is achieved by raising exceptions that inherit from `HomeAssistantError` (like `ConfigEntryAuthFailed`, `ConfigEntryNotReady`, `ServiceValidationError`, or custom ones) and providing them with `translation_domain` and `translation_key` parameters. The corresponding translation strings must then be defined in the integration's `strings.json` file under an `exceptions` block.

This rule applies to the `nest` integration because it raises several exceptions that can be surfaced to the user, for instance, during the setup process or when service calls fail.

The `nest` integration currently does **not** fully follow this rule.
1.  Several instances of `ConfigEntryAuthFailed`, `ConfigEntryNotReady`, and `HomeAssistantError` are raised with hardcoded f-strings or string literals, without using `translation_domain` or `translation_key`.
2.  In service call handlers within `climate.py`, `ValueError` is raised for input validation. These should be `ServiceValidationError` with appropriate translation keys.
3.  The `strings.json` file for the `nest` integration is missing the top-level `exceptions` block where these translations would be defined.

**Code References:**

*   **Missing `exceptions` block in `strings.json`:** The provided `homeassistant/components/nest/strings.json` does not contain an `"exceptions": {}` block.

*   **Hardcoded exceptions in `homeassistant/components/nest/__init__.py`:**
    *   Line 203: `raise ConfigEntryAuthFailed from err`
    *   Line 205: `raise ConfigEntryNotReady from err`
    *   Line 207: `raise ConfigEntryNotReady from err`
    *   Line 224: `raise ConfigEntryAuthFailed(f"Subscriber authentication error: {err!s}") from err`
    *   Line 230: `raise ConfigEntryNotReady(f"Subscriber error: {err!s}") from err`
    *   Line 236: `raise ConfigEntryNotReady(f"Device manager error: {err!s}") from err`
    *   Line 299: `raise HomeAssistantError("Unable to fetch media for event") from err`

*   **Hardcoded exceptions in `homeassistant/components/nest/camera.py`:**
    *   Line 175: `raise HomeAssistantError(f"Nest API error: {err}") from err`
    *   Line 281: `raise HomeAssistantError(f"Nest API error: {err}") from err`

*   **Incorrect exception types and hardcoded messages in `homeassistant/components/nest/climate.py` (service handlers):**
    *   Line 192: `raise ValueError(f"Unsupported hvac_mode '{hvac_mode}'")`
    *   Line 198: `raise HomeAssistantError(f"Error setting {self.entity_id} HVAC mode to {hvac_mode}: {err}") from err`
    *   Line 211: `raise HomeAssistantError(f"Error setting {self.entity_id} temperature to {kwargs}: Unable to find setpoint trait.")`
    *   Line 226: `raise HomeAssistantError(f"Error setting {self.entity_id} temperature to {kwargs}: {err}") from err`
    *   Line 231: `raise ValueError(f"Unsupported preset_mode '{preset_mode}'")`
    *   Line 237: `raise HomeAssistantError(f"Error setting {self.entity_id} preset mode to {preset_mode}: {err}") from err`
    *   Line 242: `raise ValueError(f"Unsupported fan_mode '{fan_mode}'")`
    *   Line 246: `raise ValueError("Cannot turn on fan, please set an HVAC mode (e.g. heat/cool) first")`
    *   Line 253: `raise HomeAssistantError(f"Error setting {self.entity_id} fan mode to {fan_mode}: {err}") from err`

## Suggestions

To make the `nest` integration compliant with the `exception-translations` rule, the following changes are recommended:

1.  **Add an `exceptions` block to `strings.json`:**
    Create a top-level `exceptions` block in `homeassistant/components/nest/strings.json` to hold the translatable error messages.

    ```json
    // homeassistant/components/nest/strings.json
    {
      "application_credentials": {
        // ... existing content ...
      },
      "config": {
        // ... existing content ...
      },
      // ... other top-level keys ...
      "exceptions": {
        "auth_failed_token": {
          "message": "Authentication failed, could not get access token: {error}"
        },
        "not_ready_client_response": {
          "message": "Integration not ready due to client response error: {error}"
        },
        "not_ready_client_error": {
          "message": "Integration not ready due to client error: {error}"
        },
        "auth_failed_subscriber": {
          "message": "Subscriber authentication error: {error}"
        },
        "not_ready_subscriber": {
          "message": "Subscriber error during setup: {error}"
        },
        "not_ready_device_manager": {
          "message": "Device manager error: {error}"
        },
        "fetch_media_failed": {
          "message": "Unable to fetch media for event: {error}"
        },
        "rtsp_stream_api_error": {
          "message": "Nest API error while generating RTSP stream: {error}"
        },
        "webrtc_stream_api_error": {
          "message": "Nest API error while generating WebRTC stream: {error}"
        },
        "unsupported_hvac_mode": {
          "message": "Unsupported HVAC mode: {mode}"
        },
        "set_hvac_mode_error": {
          "message": "Error setting HVAC mode to {mode}: {error}"
        },
        "set_temp_no_setpoint_trait": {
          "message": "Error setting temperature ({params}): Unable to find setpoint trait."
        },
        "set_temp_error": {
          "message": "Error setting temperature ({params}): {error}"
        },
        "unsupported_preset_mode": {
          "message": "Unsupported preset mode: {mode}"
        },
        "set_preset_mode_error": {
          "message": "Error setting preset mode to {mode}: {error}"
        },
        "unsupported_fan_mode": {
          "message": "Unsupported fan mode: {mode}"
        },
        "set_fan_mode_hvac_off_error": {
          "message": "Cannot turn on fan when HVAC mode is off. Please set an HVAC mode (e.g., heat/cool) first."
        },
        "set_fan_mode_error": {
          "message": "Error setting fan mode to {mode}: {error}"
        }
      }
    }
    ```

2.  **Update `ConfigEntryAuthFailed` and `ConfigEntryNotReady` exceptions:**
    Modify the `raise` statements in `__init__.py` to include `translation_domain`, `translation_key`, and `translation_placeholders` where appropriate.

    *Example for `__init__.py` (L224):*
    ```python
    # Before
    # raise ConfigEntryAuthFailed(f"Subscriber authentication error: {err!s}") from err

    # After
    from .const import DOMAIN  # Ensure DOMAIN is imported
    # ...
    raise ConfigEntryAuthFailed(
        translation_domain=DOMAIN,
        translation_key="auth_failed_subscriber",
        translation_placeholders={"error": str(err)},
    ) from err
    ```
    Apply similar changes to other `ConfigEntryAuthFailed` and `ConfigEntryNotReady` instances in `__init__.py`. For those without an f-string, choose an appropriate key and pass `{"error": str(err)}` as placeholders.

3.  **Update `HomeAssistantError` exceptions:**
    Modify `HomeAssistantError` raises in `__init__.py` and `camera.py` to use translation keys.

    *Example for `camera.py` (L175):*
    ```python
    # Before
    # raise HomeAssistantError(f"Nest API error: {err}") from err

    # After
    from .const import DOMAIN # Ensure DOMAIN is imported
    # ...
    raise HomeAssistantError(
        translation_domain=DOMAIN,
        translation_key="rtsp_stream_api_error",
        translation_placeholders={"error": str(err)},
    ) from err
    ```

4.  **Replace `ValueError` with `ServiceValidationError` in `climate.py` service handlers:**
    These errors occur during service calls and should be `ServiceValidationError` for proper handling and translation.

    *Example for `climate.py` (L192):*
    ```python
    # Before
    # raise ValueError(f"Unsupported hvac_mode '{hvac_mode}'")

    # After
    from homeassistant.exceptions import ServiceValidationError # Add this import
    from .const import DOMAIN # Ensure DOMAIN is imported
    # ...
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="unsupported_hvac_mode",
        translation_placeholders={"mode": hvac_mode},
    )
    ```

    *Example for `climate.py` (L198, converting existing `HomeAssistantError` to `ServiceValidationError`):*
    ```python
    # Before
    # raise HomeAssistantError(f"Error setting {self.entity_id} HVAC mode to {hvac_mode}: {err}") from err

    # After
    from homeassistant.exceptions import ServiceValidationError # Add this import
    from .const import DOMAIN # Ensure DOMAIN is imported
    # ...
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="set_hvac_mode_error",
        translation_placeholders={"mode": hvac_mode, "error": str(err)},
    ) from err
    ```
    Apply similar changes to all `ValueError` and relevant `HomeAssistantError` instances within the service call methods in `climate.py`.

By implementing these changes, exception messages will be sourced from `strings.json`, making them translatable and improving the user experience for non-English speaking users. This will satisfy the `exception-translations` rule.

_Created at 2025-05-28 23:11:58. Prompt tokens: 32411, Output tokens: 2577, Total tokens: 39362_
