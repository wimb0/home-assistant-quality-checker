# eheimdigital: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [eheimdigital](https://www.home-assistant.io/integrations/eheimdigital/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |

## Overview

The `exception-translations` rule requires that user-facing error messages are translatable. This is achieved by raising exceptions that inherit from `HomeAssistantError` (or its subclasses) and providing `translation_domain` and `translation_key` parameters. Corresponding translations must then be defined in the integration's `strings.json` file under a top-level `"exceptions"` key.

This rule applies to the `eheimdigital` integration because it interacts with hardware devices, and these interactions can fail (e.g., due to communication issues). When such failures occur during entity operations (like turning on a light, setting a temperature, or changing a value), the user should be presented with a clear, translatable error message.

The `eheimdigital` integration currently does NOT fully follow this rule.
1.  **Missing translations for existing `HomeAssistantError`s:**
    In `light.py` and `climate.py`, `EheimDigitalClientError` (a library-specific exception) is caught and re-raised as `HomeAssistantError`. However, these `HomeAssistantError` instances are raised without the required `translation_domain` and `translation_key` parameters.
    For example, in `homeassistant/components/eheimdigital/light.py` (lines 80-81, 89-90):
    ```python
    except EheimDigitalClientError as err:
        raise HomeAssistantError from err
    ```
    This results in the raw, non-translatable error message from `EheimDigitalClientError` being displayed to the user.

2.  **Unhandled library exceptions in entity methods:**
    Several entity platforms (`number.py`, `time.py`, `switch.py`, `select.py`) call methods on the `eheimdigital` library device object directly within their action methods (e.g., `async_set_native_value`, `async_set_value`, `async_turn_on`, `async_select_option`). These calls can potentially raise `EheimDigitalClientError` or other library-specific exceptions. Currently, these exceptions are not caught and re-raised as translated `HomeAssistantError`s. This can lead to unhandled exceptions and non-user-friendly error messages.
    For example, in `homeassistant/components/eheimdigital/number.py` (line 147, within the `async_set_native_value` method):
    ```python
    async def async_set_native_value(self, value: float) -> None:
        return await self.entity_description.set_value_fn(self._device, value)
    ```
    If `set_value_fn` (which calls a device method like `self._device.set_manual_speed(int(value))`) raises `EheimDigitalClientError`, it is not handled in a way that provides a translatable message to the user.

3.  **Missing `"exceptions"` section in `strings.json`:**
    The `homeassistant/components/eheimdigital/strings.json` file does not contain the required top-level `"exceptions"` key where translations for these error messages would be defined.

Config flow errors in `config_flow.py` are handled using standard Home Assistant mechanisms (`async_abort` and the `errors` dictionary for `async_show_form`), and their translations are correctly defined under the `"config"` key in `strings.json`. This part is compliant with general Home Assistant practices for config flow error handling. The "todo" status is primarily due to the handling of exceptions during entity operations.

## Suggestions

To make the `eheimdigital` integration compliant with the `exception-translations` rule, the following changes are recommended:

1.  **Add an `"exceptions"` section to `strings.json`:**
    Create a top-level `"exceptions"` key in `homeassistant/components/eheimdigital/strings.json`. Define general-purpose error keys that can be reused for common device communication failures.
    Example:
    ```json
    {
      "config": {
        // ... existing config ...
      },
      "exceptions": {
        "command_failed": {
          "message": "Failed to send command to the EHEIM device. Please check the connection and try again."
        },
        "communication_error": {
          "message": "A communication error occurred with the EHEIM device: {error_details}"
        }
        // Add more specific keys if needed
      },
      "entity": {
        // ... existing entity strings ...
      }
    }
    ```

2.  **Update existing `HomeAssistantError` usage in `light.py` and `climate.py`:**
    Modify the `except EheimDigitalClientError` blocks to include `translation_domain` and `translation_key`. Ensure `DOMAIN` from `.const` and `HomeAssistantError` from `homeassistant.exceptions` are imported.

    *   In `homeassistant/components/eheimdigital/light.py`:
        ```python
        from homeassistant.exceptions import HomeAssistantError # Ensure imported
        from .const import DOMAIN # Ensure DOMAIN is imported

        # ... inside EheimDigitalClassicLEDControlLight methods like async_turn_on, async_turn_off ...
        # Example for async_turn_on:
        # async def async_turn_on(self, **kwargs: Any) -> None:
        #     ...
        #     try:
        #         await self._device.turn_on(
        #             int(brightness_to_value(BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS])),
        #             self._channel,
        #         )
        #     except EheimDigitalClientError as err:
        #         raise HomeAssistantError(
        #             translation_domain=DOMAIN,
        #             translation_key="command_failed", 
        #             # translation_placeholders={"error_details": str(err)} # Optional, if your string needs it
        #         ) from err
        ```
    *   Repeat similar changes in `homeassistant/components/eheimdigital/climate.py` for methods like `async_set_preset_mode`, `async_set_temperature`, and `async_set_hvac_mode`.

3.  **Implement error handling in other entity platforms:**
    For platforms currently not catching `EheimDigitalClientError` (`number.py`, `time.py`, `switch.py`, `select.py`), wrap device calls in `try...except` blocks and raise translated `HomeAssistantError`s. Ensure `DOMAIN` from `.const` and `HomeAssistantError` from `homeassistant.exceptions` are imported in these files.

    *   Example for `homeassistant/components/eheimdigital/number.py` (`EheimDigitalNumber.async_set_native_value`):
        ```python
        from homeassistant.exceptions import HomeAssistantError # Add import
        from .const import DOMAIN # Add import

        # ...
        class EheimDigitalNumber(...):
            # ...
            async def async_set_native_value(self, value: float) -> None:
                try:
                    await self.entity_description.set_value_fn(self._device, value)
                except EheimDigitalClientError as err: # Assuming EheimDigitalClientError is the relevant exception
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="command_failed",
                    ) from err
        ```
    *   Apply similar `try...except` blocks to the relevant methods that perform device interactions:
        *   `homeassistant/components/eheimdigital/time.py` (in `EheimDigitalTime.async_set_value`)
        *   `homeassistant/components/eheimdigital/switch.py` (in `EheimDigitalClassicVarioSwitch.async_turn_on` and `async_turn_off`)
        *   `homeassistant/components/eheimdigital/select.py` (in `EheimDigitalSelect.async_select_option`)

**Why these changes satisfy the rule:**
By implementing these suggestions:
*   All known, user-facing exceptions arising from device interactions will be instances of `HomeAssistantError`.
*   These exceptions will carry a `translation_domain` and `translation_key`.
*   Home Assistant's core error handling mechanisms will use these keys to look up localized error messages from the `strings.json` file (under the `"exceptions"` key).
*   This ensures that users see helpful, translatable error messages, improving the usability of the integration, especially for non-English speaking users.

_Created at 2025-05-27 15:40:45. Prompt tokens: 14903, Output tokens: 2019, Total tokens: 25394_
