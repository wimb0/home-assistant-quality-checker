```markdown
# samsungtv: stale-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [stale-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/stale-devices)                                                     |
| Status | **todo**                                       |

## Overview

The `stale-devices` rule applies to integrations that manage devices in the Home Assistant device registry. The `samsungtv` integration discovers and adds individual Samsung TVs as devices to the device registry via config entries. This means the rule is applicable.

The rule requires that integrations handle the removal of devices that are no longer available. Integrations should either automatically remove devices if they can reliably obtain a list of all currently available devices, or implement the `async_remove_config_entry_device` function to allow users to manually remove devices from the UI after a check confirms the device is unavailable.

The `samsungtv` integration connects directly to a single configured TV and does not maintain a list of all possible or available Samsung TVs from a central hub or cloud service. Therefore, it cannot automatically detect if a device has become permanently unavailable (e.g., disconnected, sold, moved).

The provided code for the `samsungtv` integration, specifically in `homeassistant/components/samsungtv/__init__.py`, does not implement the `async_remove_config_entry_device` function. This function is necessary when automatic removal is not possible, enabling the "Delete" button on the device page in the UI and allowing the integration to verify if the device is truly gone before allowing removal.

Because the integration manages devices but does not implement the required manual removal hook (`async_remove_config_entry_device`), it does not fully comply with the `stale-devices` rule.

## Suggestions

To comply with the `stale-devices` rule, the `samsungtv` integration should implement the `async_remove_config_entry_device` function in `homeassistant/components/samsungtv/__init__.py`.

This function should check if the device identified by `device_entry.identifiers` is currently unreachable or confirmed unavailable by the integration. A simple check could involve attempting a quick connection or status request to the device's host. If the check indicates the device is not available, the function should return `True` to allow Home Assistant to remove the device from the registry.

Here's a suggested implementation pattern:

1.  Add the `async_remove_config_entry_device` function to `homeassistant/components/samsungtv/__init__.py`.
2.  Inside the function, extract the device identifiers (likely the unique ID based on MAC or UDN).
3.  Attempt a lightweight check to see if the device at the configured host is currently online or responding. The `SamsungTVBridge.async_is_on` method or a simple socket check could potentially be used, although care must be taken to avoid long timeouts or blocking the event loop.
4.  Return `True` if the check indicates the device is unreachable/unavailable, and `False` otherwise.

Example structure for `homeassistant/components/samsungtv/__init__.py`:

```python
# ... (existing imports and code) ...

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: SamsungTVConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    # Find the unique identifier for the device
    samsungtv_identifier = None
    for identifier in device_entry.identifiers:
        if identifier[0] == DOMAIN:
            samsungtv_identifier = identifier[1]
            break

    if not samsungtv_identifier:
        # Should not happen if device was added correctly
        LOGGER.warning("Could not find Samsung TV identifier for device %s", device_entry.id)
        return True # Allow removal if identifier is missing

    # Find the bridge associated with this config entry
    coordinator: SamsungTVDataUpdateCoordinator | None = config_entry.runtime_data
    if not coordinator:
         LOGGER.warning("Could not find coordinator for config entry %s", config_entry.entry_id)
         # Allow removal if we can't access the coordinator/bridge
         return True

    bridge = coordinator.bridge

    # Perform a lightweight check to see if the device is still reachable
    # Implement a suitable check here. For instance, try to ping or connect briefly.
    # Avoid long timeouts. This is just an example, actual implementation may vary
    # based on what the library/bridge supports for a quick status check.
    is_reachable = await bridge.async_is_on() # Or a more lightweight check

    # Return True to allow removal if the device is not reachable
    # This assumes that if the device is not online, it is safe to remove.
    LOGGER.debug("Checking reachability of device %s (%s): %s", device_entry.id, samsungtv_identifier, is_reachable)
    return not is_reachable

# ... (rest of the init.py code) ...
```

Implementing this function will satisfy the rule by providing the necessary mechanism for users to clean up stale device entries in the Home Assistant UI.
```

_Created at 2025-05-25 11:33:14. Prompt tokens: 30543, Output tokens: 1189, Total tokens: 32589_
