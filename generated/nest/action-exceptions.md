# nest: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                                                 |
| Reason | The integration does not consistently use `ServiceValidationError` for input validation failures in its climate service calls. |

## Overview

The `action-exceptions` rule requires that service actions raise specific exceptions when encountering failures: `ServiceValidationError` for incorrect user input or usage, and `HomeAssistantError` for other errors within the service action itself (e.g., API communication issues).

This rule applies to the `nest` integration as it provides services through its climate and camera entities.

The `nest` integration partially follows this rule:

*   **Compliance with `HomeAssistantError`:**
    *   Service calls that involve communication with the Nest API (e.g., setting temperature, HVAC mode, or initiating video streams) generally handle `ApiException`s from the `google-nest-sdm` library correctly by catching them and raising a `HomeAssistantError`. This is often done by wrapping the original exception, which is good practice.
        *   Example in `homeassistant/components/nest/climate.py`, `ThermostatEntity.async_set_hvac_mode()`:
            ```python
            try:
                await trait.set_mode(api_mode)
            except ApiException as err:
                raise HomeAssistantError(
                    f"Error setting {self.entity_id} HVAC mode to {hvac_mode}: {err}"
                ) from err
            ```
        *   Example in `homeassistant/components/nest/camera.py`, `NestRTSPEntity.stream_source()`:
            ```python
            try:
                self._rtsp_stream = (
                    await self._rtsp_live_stream_trait.generate_rtsp_stream()
                )
            except ApiException as err:
                raise HomeAssistantError(f"Nest API error: {err}") from err
            ```
        *   Example in `homeassistant/components/nest/camera.py`, `NestWebRTCEntity.async_handle_async_webrtc_offer()`:
            ```python
            try:
                stream = await trait.generate_web_rtc_stream(offer_sdp)
            except ApiException as err:
                raise HomeAssistantError(f"Nest API error: {err}") from err
            ```

*   **Non-compliance with `ServiceValidationError`:**
    *   Several service methods within the `ThermostatEntity` in `homeassistant/components/nest/climate.py` perform input validation but raise a standard `ValueError` instead of the required `ServiceValidationError` when validation fails.
        *   In `ThermostatEntity.async_set_hvac_mode()`:
            ```python
            if hvac_mode not in self.hvac_modes:
                raise ValueError(f"Unsupported hvac_mode '{hvac_mode}'")
            ```
        *   In `ThermostatEntity.async_set_preset_mode()`:
            ```python
            if preset_mode not in self.preset_modes:
                raise ValueError(f"Unsupported preset_mode '{preset_mode}'")
            ```
        *   In `ThermostatEntity.async_set_fan_mode()`:
            ```python
            if fan_mode not in self.fan_modes:
                raise ValueError(f"Unsupported fan_mode '{fan_mode}'")
            # ...
            if fan_mode == FAN_ON and self.hvac_mode == HVACMode.OFF:
                raise ValueError(
                    "Cannot turn on fan, please set an HVAC mode (e.g. heat/cool) first"
                )
            ```

Because `ServiceValidationError` is not used for these input validation scenarios, the integration does not fully comply with the `action-exceptions` rule.

## Suggestions

To make the `nest` integration compliant with the `action-exceptions` rule, the instances of `ValueError` raised for input validation failures in service calls should be replaced with `ServiceValidationError`.

1.  **Import `ServiceValidationError`**:
    Ensure `ServiceValidationError` is imported in `homeassistant/components/nest/climate.py`:
    ```python
    from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
    ```

2.  **Modify `ThermostatEntity.async_set_hvac_mode()`**:
    Change:
    ```python
    if hvac_mode not in self.hvac_modes:
        raise ValueError(f"Unsupported hvac_mode '{hvac_mode}'")
    ```
    To (consider adding more context to the error message):
    ```python
    if hvac_mode not in self.hvac_modes:
        raise ServiceValidationError(
            f"Unsupported HVAC mode '{hvac_mode}' for entity {self.entity_id}. "
            f"Supported modes: {self.hvac_modes}"
        )
    ```

3.  **Modify `ThermostatEntity.async_set_preset_mode()`**:
    Change:
    ```python
    if preset_mode not in self.preset_modes:
        raise ValueError(f"Unsupported preset_mode '{preset_mode}'")
    ```
    To (consider adding more context):
    ```python
    if preset_mode not in self.preset_modes:
        raise ServiceValidationError(
            f"Unsupported preset mode '{preset_mode}' for entity {self.entity_id}. "
            f"Supported presets: {self.preset_modes}"
        )
    ```

4.  **Modify `ThermostatEntity.async_set_fan_mode()`**:
    Change:
    ```python
    if fan_mode not in self.fan_modes:
        raise ValueError(f"Unsupported fan_mode '{fan_mode}'")
    ```
    To (consider adding more context):
    ```python
    if fan_mode not in self.fan_modes:
        raise ServiceValidationError(
            f"Unsupported fan mode '{fan_mode}' for entity {self.entity_id}. "
            f"Supported fan modes: {self.fan_modes}"
        )
    ```
    And change:
    ```python
    if fan_mode == FAN_ON and self.hvac_mode == HVACMode.OFF:
        raise ValueError(
            "Cannot turn on fan, please set an HVAC mode (e.g. heat/cool) first"
        )
    ```
    To:
    ```python
    if fan_mode == FAN_ON and self.hvac_mode == HVACMode.OFF:
        raise ServiceValidationError(
            f"Cannot turn on fan for entity {self.entity_id} when HVAC mode is OFF. "
            "Please set an HVAC mode (e.g., heat/cool) first."
        )
    ```

**Why these changes satisfy the rule:**
Replacing `ValueError` with `ServiceValidationError` aligns the integration with the rule's requirement to use specific exception types for different failure scenarios. `ServiceValidationError` is designated for issues arising from incorrect user input or service usage, allowing Home Assistant to handle these errors appropriately and potentially provide more specific feedback to the user in the UI.

_Created at 2025-05-28 22:54:05. Prompt tokens: 32353, Output tokens: 1671, Total tokens: 38142_
