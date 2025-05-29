# nest: stale-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [stale-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/stale-devices)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `stale-devices` rule applies to the Nest integration as it manages devices (thermostats, cameras, etc.) linked to a Google Nest account, which can be removed or become unavailable.

The integration currently does not fully follow this rule for two main reasons:

1.  **Automatic Stale Device Removal:** The integration handles changes in device availability (e.g., a device removed from the Nest account) by listening for a `relation_update` event from the Nest SDM Pub/Sub stream. As seen in `homeassistant/components/nest/__init__.py` within the `SignalUpdateCallback.async_handle_event` method:
    ```python
    if event_message.relation_update:
        _LOGGER.info("Devices or homes have changed; Need reload to take effect")
        # This callback (self._config_reload_cb) eventually calls:
        # await hass.config_entries.async_reload(entry.entry_id)
        return
    ```
    When such an event occurs, the integration triggers a full reload of its configuration entry. While a reload will cause Home Assistant to re-evaluate the devices provided by the integration (and core HA logic might eventually remove devices no longer set up by the entry), this is an indirect mechanism. The rule's preferred pattern involves the integration actively identifying stale devices (e.g., by comparing a new list of devices from the API with a previous list) and then explicitly calling `device_registry.async_update_device(..., remove_config_entry_id=...)` for each stale device. The Nest integration does not implement this explicit, targeted removal.

2.  **Manual Device Removal:** The integration does not implement the `async_remove_config_entry_device` function in its `__init__.py`. This function is crucial as it allows users to manually remove a device from Home Assistant via the device page in the UI. This is particularly important if the automatic detection of stale devices (via `relation_update` and reload) is delayed, fails, or if a device becomes permanently unresponsive but isn't immediately removed from the Google account. Without this function, users have no straightforward way to clean up such stale device entries.

Therefore, because the integration lacks both a direct mechanism for automatic stale device removal and the fallback manual removal option, it does not fully comply with the `stale-devices` rule.

## Suggestions

To make the Nest integration compliant with the `stale-devices` rule, the following changes are recommended:

1.  **Implement `async_remove_config_entry_device`:**
    This is the most critical change to allow users to manually remove devices that the integration might not automatically clean up. Add the following function to `homeassistant/components/nest/__init__.py`:

    ```python
    from homeassistant.helpers import device_registry as dr

    # ... other imports

    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: NestConfigEntry, device_entry: dr.DeviceEntry
    ) -> bool:
        """Remove a Nest device from a config entry."""
        if not config_entry.runtime_data or not config_entry.runtime_data.device_manager:
            # Integration data not loaded, disallow removal to be safe.
            # Or, if always false, user can never remove. Consider if this state is possible
            # when a user would want to remove. If device_manager is gone, likely safe.
            _LOGGER.warning(
                "Attempted to remove device %s but Nest runtime data is not available.",
                device_entry.id,
            )
            return False

        current_nest_device_ids = {
            device.name
            for device in config_entry.runtime_data.device_manager.devices.values()
        }

        for identifier in device_entry.identifiers:
            if identifier[0] == DOMAIN:
                nest_api_device_id = identifier[1]
                # If the device is still reported by the Nest API via the device manager,
                # it's considered active, so disallow manual removal.
                if nest_api_device_id in current_nest_device_ids:
                    _LOGGER.debug(
                        "Device %s (API ID: %s) is still active, disallowing manual removal.",
                        device_entry.id,
                        nest_api_device_id,
                    )
                    return False
        
        # If we reach here, none of the device's identifiers (for the Nest domain)
        # match a currently active device known to the device manager.
        # This means the device is stale from the integration's perspective.
        _LOGGER.debug(
            "Device %s is no longer active, allowing manual removal.", device_entry.id
        )
        return True

    ```
    This implementation checks if the device associated with `device_entry` is still present in the `device_manager`'s current list of devices. If it's not found, it means the device is likely stale (no longer reported by the API for this config entry), and the function returns `True`, enabling the "Delete" button in the UI.

2.  **(Optional Enhancement) Implement Explicit Automatic Removal:**
    If the `event_message.relation_update` in `SignalUpdateCallback.async_handle_event` can provide specific information about which devices were removed (rather than just a generic "something changed"), consider modifying the handler to perform explicit removal:
    *   Instead of a full config entry reload for device removals, identify the specific `device_id`(s) that were removed.
    *   Get the `DeviceRegistry`.
    *   For each removed Nest API device ID, find the corresponding `DeviceEntry` in Home Assistant.
    *   Call `device_registry.async_update_device(ha_device_entry.id, remove_config_entry_id=self._config_entry.entry_id)`.
    This would align more closely with the rule's primary example for automatic stale device handling and could be more efficient than a full reload. However, if the `relation_update` event lacks this granularity, the current reload mechanism combined with the suggested `async_remove_config_entry_device` would be a compliant approach.

Implementing `async_remove_config_entry_device` is the primary step towards compliance, as it addresses the case where automatic removal might not be immediate or sufficient.

_Created at 2025-05-28 23:17:14. Prompt tokens: 32769, Output tokens: 1525, Total tokens: 38436_
