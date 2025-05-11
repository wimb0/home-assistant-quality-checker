# wled: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `action-exceptions` rule mandates that service actions should raise appropriate exceptions when failures occur: `ServiceValidationError` for incorrect user input or referencing non-existent items, and `HomeAssistantError` for other issues like network errors or internal service bugs.

The `wled` integration defines multiple service actions across its entities (lights, switches, selects, numbers, buttons, update). These actions primarily interact with the WLED device through the `wled` Python library.

Most service action methods in the `wled` integration are decorated with a custom `@wled_exception_handler` (defined in `helpers.py`). This handler is designed to catch exceptions from the `wled` library:
```python
# helpers.py
def wled_exception_handler[...](...):
    # ...
    async def handler(self: _WLEDEntityT, *args: _P.args, **kwargs: _P.kwargs) -> None:
        try:
            await func(self, *args, **kwargs)
            # ...
        except WLEDConnectionError as error:
            # ...
            raise HomeAssistantError("Error communicating with WLED API") from error
        except WLEDError as error: # Catches base WLEDError and its subclasses
            raise HomeAssistantError("Invalid response from WLED API") from error
    return handler
```

This handler correctly raises `HomeAssistantError` when a `WLEDConnectionError` (e.g., network issue) or a generic `WLEDError` (e.g., unexpected device response, internal device error) occurs. This fulfills part of the rule concerning "an error in the service action itself".

However, the rule also specifies that `ServiceValidationError` should be raised "when the problem is caused by incorrect usage (for example incorrect input or referencing something that does not exist)". The current `wled_exception_handler` does not distinguish these types of errors. If the `wled` library raises an exception because a user provided, for instance, a non-existent effect name, preset name, or color palette name, this error (assuming it's a subclass of `WLEDError`) would be caught and re-raised as a generic `HomeAssistantError("Invalid response from WLED API")`.

For example, in `select.py`, `WLEDPresetSelect.async_select_option`:
```python
    @wled_exception_handler
    async def async_select_option(self, option: str) -> None:
        """Set WLED segment to the selected preset."""
        await self.coordinator.wled.preset(preset=option)
```
If `option` refers to a preset that doesn't exist on the WLED device, the `wled.preset()` call would likely raise an error. The `wled_exception_handler` would convert this into a `HomeAssistantError`. According to the rule, this scenario ("referencing something that does not exist") should ideally result in a `ServiceValidationError`.

While the integration *does* raise exceptions for failures, it does not consistently use the more specific `ServiceValidationError` for user input or non-existent resource errors that are detected by the WLED device/library. This means the feedback to the user might be less precise than intended by the rule.

Therefore, the integration partially follows the rule by raising `HomeAssistantError` for device/API issues but needs improvement in raising `ServiceValidationError` for relevant input errors.

## Suggestions

To fully comply with the `action-exceptions` rule, the integration should differentiate between general API/device errors and errors caused by invalid user input or referencing non-existent resources.

1.  **Identify Specific Library Exceptions:**
    Investigate the `wled` Python library (version `0.21.0` as per `manifest.json`) to identify if it raises distinct exception types for errors such as "effect not found," "preset not found," "palette not found," "invalid segment ID," or other input validation failures that are not mere connection issues.

2.  **Refine Exception Handling:**
    Modify the `wled_exception_handler` in `helpers.py`, or add more specific `try...except` blocks directly within the service methods that handle user-provided identifiers (like names of effects, presets, palettes).

    If the `wled` library provides specific exceptions for "not found" or "invalid input" scenarios, catch these explicitly and raise a `ServiceValidationError`. The message for `ServiceValidationError` should be user-friendly, clearly indicating the nature of the input error, and ideally use translatable strings if they are common errors.

    **Example (conceptual modification to `wled_exception_handler` or in service methods):**
    ```python
    from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
    # Assuming 'wled' library has specific errors like:
    # from wled import WLEDPresetNotFoundError, WLEDEffectNotFoundError, WLEDInvalidInputError (hypothetical)

    # ... inside the try block of the handler or service method ...
    # await func(self, *args, **kwargs) or await self.coordinator.wled.call(...)
    # ...

    # Example for specific error types from the wled library:
    except wled.WLEDPresetNotFoundError as err: # Hypothetical exception
        # 'preset_name' would be the input 'option' from the service call
        raise ServiceValidationError(
            f"The WLED preset '{err.name_or_id_attempted}' could not be found on the device."
        ) from err
    except wled.WLEDEffectNotFoundError as err: # Hypothetical exception
        raise ServiceValidationError(
            f"The WLED effect '{err.name_or_id_attempted}' could not be found on the device."
        ) from err
    # Add other specific "not found" or "invalid input" WLED exceptions here

    except WLEDConnectionError as err:
        # Current handling is appropriate
        raise HomeAssistantError("Error communicating with WLED API") from err
    except WLEDError as err: # Catch-all for other WLED library errors
        # Current handling is a fallback
        # Consider making the message more informative if err contains useful details
        raise HomeAssistantError(f"An error occurred with the WLED device: {err}") from err
    ```

3.  **Apply to Relevant Services:**
    This refined error handling should be applied to service actions where users provide names or identifiers, such as:
    *   `LightEntity.async_turn_on` (for `ATTR_EFFECT`)
    *   `SelectEntity.async_select_option` (for presets, playlists, color palettes)
    *   `UpdateEntity.async_install` (if a specific version is not found)

By implementing these changes, the `wled` integration will provide more accurate and actionable error feedback to users, distinguishing between problems with their input and general device or communication failures, thus fully adhering to the `action-exceptions` rule.

_Created at 2025-05-10 22:53:12. Prompt tokens: 21350, Output tokens: 1645, Total tokens: 29656_
