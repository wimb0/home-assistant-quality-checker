# linkplay: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `action-exceptions` rule mandates that service actions must raise specific Home Assistant exceptions when failures are encountered: `ServiceValidationError` for issues caused by incorrect usage or input, and `HomeAssistantError` for errors within the service action itself (e.g., network failures, device errors).

This rule applies to the `linkplay` integration as it registers a custom service (`play_preset`) and implements standard entity service methods (e.g., `select_source`, `set_volume_level` for media players).

The integration partially follows this rule:
1.  **Good:** It utilizes a decorator `exception_wrap` (in `entity.py`) which catches `LinkPlayRequestException` (the library's specific exception for communication/API errors) and re-raises it as a `HomeAssistantError`. This correctly handles device communication failures for many actions, aligning with the rule's requirement for internal/service errors.
    ```python
    # entity.py
    def exception_wrap(...):
        # ...
        except LinkPlayRequestException as err:
            raise HomeAssistantError(
                f"Exception occurred when communicating with API {func}: {err}"
            ) from err
    ```
2.  **Good:** The `async_join_players` method in `media_player.py` correctly raises a `ServiceValidationError` if an invalid `entity_id` is provided for grouping, which is an example of incorrect usage.
    ```python
    # media_player.py
    async def _get_linkplay_bridge(self, entity_id: str) -> LinkPlayBridge:
        # ...
        if bridge is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_grouping_entity",
                translation_placeholders={"entity_id": entity_id},
            )
    ```

However, there are areas where the integration does not fully comply:

1.  **Incorrect Exception Type for Custom Service:** The `async_play_preset` service method in `media_player.py` handles `ValueError` (raised by the `linkplay` library for an invalid preset number, e.g., out of the 1-10 range) by re-raising it as a generic `HomeAssistantError`. According to the rule, an invalid preset number is "incorrect input" and should result in a `ServiceValidationError`.
    ```python
    # media_player.py
    @exception_wrap
    async def async_play_preset(self, preset_number: int) -> None:
        """Play preset number."""
        try:
            await self._bridge.player.play_preset(preset_number)
        except ValueError as err: # Indicates invalid preset from the library
            raise HomeAssistantError(err) from err # Should be ServiceValidationError
    ```

2.  **Missing Error Handling for Standard Service Methods:** Several standard service methods in `media_player.py`, such as `async_select_source`, `async_select_sound_mode`, and `async_set_repeat`, involve looking up values in mapping dictionaries (e.g., `SOURCE_MAP_INV`) and then calling library functions that might raise `ValueError` if the provided argument is not supported by the device (even if it's a valid choice from `source_list`).
    *   If an invalid key is used for these lookups (e.g., `SOURCE_MAP_INV[source]`), a `KeyError` would occur.
    *   If the library call (e.g., `self._bridge.player.set_play_mode(play_mode)`) raises a `ValueError` because the mode is unsupported by the specific device.
    Currently, these `KeyError` or `ValueError` exceptions are not explicitly caught and converted to `ServiceValidationError`. The `exception_wrap` decorator only catches `LinkPlayRequestException`, so these errors would propagate unhandled or as raw exceptions, not user-friendly Home Assistant exceptions. These scenarios also represent "incorrect input" or "referencing something that does not exist" (or is not applicable) and should raise `ServiceValidationError`.
    For example, in `async_select_source`:
    ```python
    # media_player.py
    @exception_wrap
    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        # Potential KeyError if source is invalid and bypasses HA core validation
        # Potential ValueError from set_play_mode if library rejects the mode
        await self._bridge.player.set_play_mode(SOURCE_MAP_INV[source])
    ```

## Suggestions

To make the `linkplay` integration compliant with the `action-exceptions` rule, the following changes are recommended:

1.  **Modify `async_play_preset` to raise `ServiceValidationError` for invalid presets:**
    In `media_player.py`, change the exception handling for `ValueError` in the `async_play_preset` method.

    *Current code:*
    ```python
    # media_player.py
    @exception_wrap
    async def async_play_preset(self, preset_number: int) -> None:
        """Play preset number."""
        try:
            await self._bridge.player.play_preset(preset_number)
        except ValueError as err:
            raise HomeAssistantError(err) from err
    ```

    *Suggested code (using a direct string, translation preferred):*
    ```python
    # media_player.py
    from homeassistant.exceptions import HomeAssistantError, ServiceValidationError # Ensure ServiceValidationError is imported

    # ...

    @exception_wrap
    async def async_play_preset(self, preset_number: int) -> None:
        """Play preset number."""
        try:
            await self._bridge.player.play_preset(preset_number)
        except ValueError as err:
            # ValueError from python-linkplay's play_preset indicates an invalid preset number (e.g., out of range 1-10)
            raise ServiceValidationError(
                f"Invalid preset number: {preset_number}. The device reported: {err}"
            ) from err
        # LinkPlayRequestException for communication errors is handled by @exception_wrap
    ```
    *Alternatively, using a translation string (best practice):*
    First, add a new translation key to `strings.json`:
    ```json
    // strings.json
    {
      // ...
      "exceptions": {
        "invalid_grouping_entity": {
          "message": "Entity with ID {entity_id} can't be added to the LinkPlay multiroom. Is the entity a LinkPlay media player?"
        },
        "invalid_preset_number": {  // New key
          "message": "Invalid preset number: {preset_number}. Presets must be between 1 and 10 for this device."
        }
        // ...
      }
    }
    ```
    Then, update the method:
    ```python
    # media_player.py
    # ... (imports)
    from .const import DOMAIN # Ensure DOMAIN is available if not already

    @exception_wrap
    async def async_play_preset(self, preset_number: int) -> None:
        """Play preset number."""
        try:
            await self._bridge.player.play_preset(preset_number)
        except ValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_preset_number",
                translation_placeholders={"preset_number": str(preset_number)},
            ) from err
    ```
    **Reasoning:** This change ensures that user errors (providing an invalid preset number) are reported with `ServiceValidationError`, as per the rule.

2.  **Add specific error handling in standard service methods:**
    For methods like `async_select_source`, `async_select_sound_mode`, and `async_set_repeat` in `media_player.py`, add `try...except` blocks to catch `KeyError` (from dictionary lookups) and `ValueError` (from library calls for setting modes/options) and raise `ServiceValidationError`.

    *Example for `async_select_source`:*
    ```python
    # media_player.py
    @exception_wrap
    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        try:
            play_mode = SOURCE_MAP_INV[source]
        except KeyError as err:
            # This source is not in SOURCE_MAP_INV, meaning it's not a known, mappable source.
            # This should ideally be caught by HA's service validation against `source_list`.
            # If it gets here, it's an invalid input.
            raise ServiceValidationError(
                f"Invalid source specified: '{source}'. Supported sources for this entity: {self.source_list}"
            ) from err
        
        try:
            await self._bridge.player.set_play_mode(play_mode)
        except ValueError as err:
            # The library itself rejected the play_mode (e.g., device doesn't support it for some reason)
            raise ServiceValidationError(
                f"Cannot set source to '{source}' for this device. The device reported: {err}"
            ) from err
        # LinkPlayRequestException for communication errors is handled by @exception_wrap
    ```
    Similar logic should be applied to `async_select_sound_mode` (for `EQUALIZER_MAP_INV` and `set_equalizer_mode`) and `async_set_repeat` (for `REPEAT_MAP_INV` and `set_loop_mode`).
    **Reasoning:** This ensures that if a user attempts to set an invalid source, sound mode, or repeat mode (that might pass initial Home Assistant validation but is rejected by the library or device logic), a `ServiceValidationError` is raised, clearly indicating an issue with the provided parameters.

By implementing these suggestions, the `linkplay` integration will more robustly handle errors in its service actions and align fully with the `action-exceptions` quality scale rule.

_Created at 2025-05-11 14:56:33. Prompt tokens: 10735, Output tokens: 2384, Total tokens: 19940_
