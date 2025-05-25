```markdown
# samsungtv: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |

## Overview

This rule requires that any exception messages shown to the user, especially those originating from `HomeAssistantError` or its subclasses, must be translatable. This is achieved by providing `translation_domain` and `translation_key` when raising the exception, with the corresponding message defined in the integration's `strings.json` file.

The `samsungtv` integration generally follows this rule for many user-facing exceptions. For example:

*   In `homeassistant/components/samsungtv/__init__.py`, `ConfigEntryAuthFailed` is raised with `translation_domain` and `translation_key`.
*   In `homeassistant/components/samsungtv/entity.py`, a `HomeAssistantError` is raised in `async_turn_on` with `translation_domain`, `translation_key`, and `translation_placeholders`.
*   In `homeassistant/components/samsungtv/media_player.py`, `HomeAssistantError` instances are raised in `async_set_volume_level` and `async_select_source` with translation information.
*   In `homeassistant/components/samsungtv/bridge.py`, `HomeAssistantError` is raised in the legacy `_send_key` method with translation information.

All these cases correctly reference keys that exist in the `exceptions` section of `homeassistant/components/samsungtv/strings.json`.

However, the rule is not fully followed in the device trigger validation and attachment code (`homeassistant/components/samsungtv/triggers/turn_on.py`). Several helper functions in `homeassistant/components/samsungtv/helpers.py` raise `ValueError` with descriptive messages (e.g., "Device {device_id} is not a valid samsungtv device."). These `ValueError` instances are then caught in `triggers/turn_on.py` and re-raised as `InvalidDeviceAutomationConfig` (a subclass of `HomeAssistantError`), but without providing the `translation_domain` or `translation_key`. This results in the original, untranslated `ValueError` message being used for the user-facing error related to invalid device or entity IDs in trigger configuration.

For instance, in `homeassistant/components/samsungtv/triggers/turn_on.py`:

```python
        except ValueError as err:
            raise InvalidDeviceAutomationConfig(err) from err
```
This pattern prevents the error message from being translated according to the standard Home Assistant mechanism for `HomeAssistantError`.

Therefore, the integration does not fully comply with the rule.

## Suggestions

To comply with the `exception-translations` rule, the integration should ensure that all user-facing errors derived from `HomeAssistantError` (or its subclasses) are translatable.

1.  **Modify Helper Functions:** Update the helper functions in `homeassistant/components/samsungtv/helpers.py` that currently raise `ValueError` to instead raise a subclass of `HomeAssistantError` (such as `InvalidDeviceAutomationConfig` from `homeassistant.components.device_automation`) and include the `translation_domain`, `translation_key`, and necessary `translation_placeholders`.

    *   Add new keys to the `exceptions` section in `homeassistant/components/samsungtv/strings.json` for these specific errors, e.g.:
        ```json
        "invalid_device_id": {
          "message": "Device {device_id} is not a valid Samsung TV device."
        },
        "invalid_entity_id": {
          "message": "Entity {entity_id} is not a valid Samsung TV entity."
        },
        "device_not_linked_to_config_entry": {
          "message": "Device {device_id} is not from an existing Samsung TV config entry."
        }
        ```
    *   Update the helper functions (e.g., `async_get_device_entry_by_device_id`, `async_get_device_id_from_entity_id`, `async_get_client_by_device_entry`) to use these keys:
        ```python
        # Example change in homeassistant/components/samsungtv/helpers.py
        from homeassistant.components.device_automation import InvalidDeviceAutomationConfig
        # ...

        @callback
        def async_get_device_entry_by_device_id(
            hass: HomeAssistant, device_id: str
        ) -> DeviceEntry:
            """Get Device Entry from Device Registry by device ID.

            Raises InvalidDeviceAutomationConfig if device ID is invalid.
            """
            device_reg = dr.async_get(hass)
            if (device := device_reg.async_get(device_id)) is None:
                raise InvalidDeviceAutomationConfig(
                    translation_domain=DOMAIN,
                    translation_key="invalid_device_id",
                    translation_placeholders={"device_id": device_id},
                )
            return device

        # Apply similar changes to async_get_device_id_from_entity_id and async_get_client_by_device_entry
        ```

2.  **Simplify Error Handling in Trigger Code:** Once the helper functions raise translatable exceptions, the `try...except ValueError` blocks in `homeassistant/components/samsungtv/triggers/turn_on.py` can be removed or simplified to catch the appropriate `HomeAssistantError` subclass and simply re-raise it, as it already contains the translation information. For example:

    ```python
    # Example change in homeassistant/components/samsungtv/triggers/turn_on.py
    from homeassistant.components.device_automation import InvalidDeviceAutomationConfig
    # ...

    async def async_validate_trigger_config(
        hass: HomeAssistant, config: ConfigType
    ) -> ConfigType:
        """Validate config."""
        config = TRIGGER_SCHEMA(config)

        if config[CONF_TYPE] == TURN_ON_PLATFORM_TYPE:
            device_id = config[CONF_DEVICE_ID]
            # Catch the specific translatable error from the helper
            try:
                device = async_get_device_entry_by_device_id(hass, device_id)
                async_get_client_by_device_entry(hass, device) # Also raises a translatable error now
            except InvalidDeviceAutomationConfig:
                 # Re-raise the exception which already has translation info
                 raise

        return config
    ```
    Apply similar logic to the `async_attach_trigger` function if it also catches `ValueError` from these helpers.

These changes will ensure that trigger validation errors are also translatable, aligning the integration with the `exception-translations` rule.
```

_Created at 2025-05-25 11:32:30. Prompt tokens: 30185, Output tokens: 1586, Total tokens: 35596_
