# zimi: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [zimi](https://www.home-assistant.io/integrations/zimi/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `action-exceptions` rule requires that service actions raise specific Home Assistant exceptions (`ServiceValidationError` or `HomeAssistantError`) when they encounter failures. This ensures that users receive clear, actionable feedback in the UI.

This rule **applies** to the `zimi` integration. Entity methods that are called as a result of service invocations (e.g., `light.turn_on` service calling the `async_turn_on` method of a light entity) are considered "service actions" in this context. These methods interact with the Zimi devices via the `zcc-helper` library and can encounter errors (e.g., network issues, device unavailability, command failures).

The `zimi` integration currently does **not** follow this rule. The methods responsible for device actions (e.g., turning on/off, setting brightness/speed) in `fan.py`, `light.py`, and `switch.py` make calls to the underlying `self._device` (an instance from the `zcc-helper` library) without wrapping these calls in `try...except` blocks to catch potential errors and re-raise them as `HomeAssistantError`.

For example:
*   In `fan.py`, `ZimiFan.async_set_percentage`:
    ```python
    # ...
    await self._device.set_fanspeed(target_speed)
    ```
*   In `light.py`, `ZimiLight.async_turn_on`:
    ```python
    # ...
    await self._device.turn_on()
    ```
*   In `switch.py`, `ZimiSwitch.async_turn_on`:
    ```python
    # ...
    await self._device.turn_on()
    ```

If methods like `self._device.set_fanspeed()` or `self._device.turn_on()` (from the `zcc-helper` library) raise an exception (e.g., `ControlPointError` or a subclass, which is used elsewhere in the integration for connection errors, or other I/O related errors), these exceptions will propagate uncaught by the integration's action methods. This can lead to unhandled exceptions or library-specific error messages being shown to the user, rather than a clear `HomeAssistantError`.

The integration does not currently use `ServiceValidationError` in its action methods. While Home Assistant's core handles basic type and range validation for standard services, `ServiceValidationError` could be used if there were specific, knowable invalid input combinations for Zimi devices that could be checked before attempting a command. However, the primary omission is the handling of runtime errors with `HomeAssistantError`.

The `quality_scale.yaml` file for this integration already correctly identifies this rule with a status of `todo`.

## Suggestions

To comply with the `action-exceptions` rule, the integration should modify its entity action methods to catch exceptions from the `zcc-helper` library and re-raise them as `HomeAssistantError`.

1.  **Import necessary exceptions:**
    Ensure `HomeAssistantError` (and `ServiceValidationError` if applicable) is imported from `homeassistant.exceptions`. Also, import relevant error types from the `zcc` library, likely `ControlPointError` as it's used for connection issues in `__init__.py` and `config_flow.py`.

    ```python
    # At the top of fan.py, light.py, switch.py
    from homeassistant.exceptions import HomeAssistantError # Potentially ServiceValidationError
    from zcc import ControlPointError # Or more specific exceptions if the library provides them for device operations
    import logging # if not already imported for _LOGGER

    _LOGGER = logging.getLogger(__name__) # if not already defined
    ```

2.  **Wrap device communication calls:**
    In each method that interacts with `self._device` to perform an action (e.g., `async_turn_on`, `async_turn_off`, `async_set_percentage`, `async_set_brightness`), wrap the call in a `try...except` block.

    *   Catch specific exceptions from the `zcc-helper` library (e.g., `ControlPointError` or subclasses).
    *   Raise a `HomeAssistantError` with a user-friendly message, including the original error information using `from err`.
    *   Consider a general `except Exception` as a fallback for unexpected errors from the library, logging them and raising a generic `HomeAssistantError`.

**Example for `ZimiFan.async_set_percentage` in `fan.py`:**
```python
async def async_set_percentage(self, percentage: int) -> None:
    """Set the desired speed for the fan."""

    if percentage == 0:
        # Ensure async_turn_off also handles exceptions properly
        await self.async_turn_off()
        return

    target_speed = math.ceil(
        percentage_to_ranged_value(self._attr_speed_range, percentage)
    )

    _LOGGER.debug(
        "Sending async_set_percentage() for %s with percentage %s",
        self.name,
        percentage,
    )

    try:
        await self._device.set_fanspeed(target_speed)
    except ControlPointError as err: # Catch known library errors
        _LOGGER.error("Error setting fan speed for %s: %s", self.name, err)
        raise HomeAssistantError(
            f"Failed to set fan speed for '{self.name}'. The device may be offline or unreachable. Error: {err}"
        ) from err
    except Exception as err: # Catch unexpected errors
        _LOGGER.exception(
            "Unexpected error while setting fan speed for %s", self.name
        )
        raise HomeAssistantError(
            f"An unexpected error occurred while setting fan speed for '{self.name}'."
        ) from err
```

**Example for `ZimiLight.async_turn_on` in `light.py`:**
```python
async def async_turn_on(self, **kwargs: Any) -> None:
    """Instruct the light to turn on."""

    _LOGGER.debug(
        "Sending turn_on() for %s in %s", self._device.name, self._device.room
    )

    try:
        await self._device.turn_on()
    except ControlPointError as err: # Catch known library errors
        _LOGGER.error("Error turning on light %s: %s", self.name, err)
        raise HomeAssistantError(
            f"Failed to turn on light '{self.name}'. The device may be offline or unreachable. Error: {err}"
        ) from err
    except Exception as err: # Catch unexpected errors
        _LOGGER.exception(
            "Unexpected error while turning on light %s", self.name
        )
        raise HomeAssistantError(
            f"An unexpected error occurred while turning on light '{self.name}'."
        ) from err
```

3.  **Apply consistently:**
    This pattern should be applied to all action methods across `fan.py`, `light.py`, and `switch.py`:
    *   `ZimiFan`: `async_set_percentage`, `async_turn_on`, `async_turn_off`.
    *   `ZimiLight`: `async_turn_on`, `async_turn_off`.
    *   `ZimiDimmer`: `async_turn_on` (which calls `self._device.set_brightness`).
    *   `ZimiSwitch`: `async_turn_on`, `async_turn_off`.

By implementing these changes, the `zimi` integration will provide clearer error feedback to users when device actions fail, adhering to the `action-exceptions` rule. If there are specific input validations that can be performed before calling the library for which `ServiceValidationError` would be appropriate, those should also be considered, but the immediate need is handling runtime/communication errors with `HomeAssistantError`.

_Created at 2025-05-14 14:49:36. Prompt tokens: 7666, Output tokens: 1902, Total tokens: 15085_
