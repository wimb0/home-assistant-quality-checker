# overkiz: stale-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [stale-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/stale-devices)                                                     |
| Status | **todo**                                       |
| Reason | Integration is missing some mechanisms for handling stale devices as per the rule requirements. |

## Overview

The `stale-devices` rule requires that devices removed from the external hub or account are also removed from Home Assistant. If the integration cannot be certain a device is gone, it should implement `async_remove_config_entry_device` to allow users to remove devices manually.

The `overkiz` integration handles devices that can be added or removed from an external system (Somfy TaHoma, Cozytouch, etc.), so this rule **applies**.

The integration currently has partial support for this rule but has some gaps:

1.  **Automatic Removal via Events**:
    *   The integration listens for `EventName.DEVICE_REMOVED` events from the Overkiz API. The `on_device_removed` handler in `homeassistant/components/overkiz/coordinator.py` attempts to remove the device:
        ```python
        # homeassistant/components/overkiz/coordinator.py
        @EVENT_HANDLERS.register(EventName.DEVICE_REMOVED)
        async def on_device_removed(
            coordinator: OverkizDataUpdateCoordinator, event: Event
        ) -> None:
            # ...
            if registered_device := registry.async_get_device(
                identifiers={(DOMAIN, base_device_url)}
            ):
                registry.async_remove_device(registered_device.id) # <-- Uses direct removal
            # ...
            if event.device_url:
                del coordinator.devices[event.device_url]
        ```
    *   This handles devices removed while Home Assistant is connected and actively receiving events.
    *   However, it uses `device_registry.async_remove_device()`, which is a direct, hard deletion. The rule's example and common Home Assistant practice prefer using `device_registry.async_update_device(device_id=device.id, remove_config_entry_id=config_entry.entry_id)`. This "soft" removal marks the device as no longer provided by the config entry, allowing Home Assistant to manage its lifecycle more gracefully, especially if other integrations might theoretically manage the same device or for cleanup routines.

2.  **Missing Automatic Removal on Full Refresh**:
    *   If a device is removed from the Overkiz hub/account while Home Assistant is offline or disconnected, the `DEVICE_REMOVED` event might be missed.
    *   When Home Assistant starts or reconnects, `async_setup_entry` (in `__init__.py`) or the re-login logic in `coordinator._async_update_data` fetches a full list of current devices via `client.get_setup()` or `client.get_devices()`.
    *   Currently, there is **no logic to compare this fresh list of devices with those already in Home Assistant's device registry for this config entry**. Stale devices (present in the registry but not in the fresh list from the API) are not cleaned up automatically during these full refresh scenarios.

3.  **Missing Manual Removal Capability**:
    *   The integration does **not** implement the `async_remove_config_entry_device` function in `homeassistant/components/overkiz/__init__.py`.
    *   This means users cannot manually remove a device from the Home Assistant UI if it becomes stale and is not automatically cleaned up (e.g., due to the gaps mentioned above).

Due to the lack of comprehensive automatic cleanup during full refreshes and the absence of a manual removal option, the integration does not fully comply with the `stale-devices` rule.

## Suggestions

To make the `overkiz` integration compliant with the `stale-devices` rule, the following changes are recommended:

1.  **Implement `async_remove_config_entry_device` for manual removal:**
    Add the following function to `homeassistant/components/overkiz/__init__.py`. This will enable the "DELETE" button on the device page in Home Assistant, allowing users to remove devices that the integration fails to clean up automatically.

    ```python
    # homeassistant/components/overkiz/__init__.py
    # ... (other imports)
    from homeassistant.helpers import device_registry as dr
    from typing import cast # Add this if not present

    # ... (rest of the file)

    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
    ) -> bool:
        """Remove an Overkiz device from a config entry."""
        # Ensure that runtime_data for the config entry is loaded.
        # The HomeAssistantOverkizData contains the coordinator.
        try:
            overkiz_data = cast(HomeAssistantOverkizData, hass.data[DOMAIN][config_entry.entry_id])
            coordinator = overkiz_data.coordinator
        except KeyError:
            # Config entry not fully loaded or data structure is unexpected.
            # Disallow removal if coordinator cannot be accessed.
            LOGGER.warning(
                "Attempted to remove device %s for Overkiz config entry %s that is not fully loaded.",
                device_entry.id,
                config_entry.entry_id
            )
            return False

        # device_entry.identifiers typically contains a tuple like (DOMAIN, "base_device_url")
        # coordinator.data (same as coordinator.devices) has keys as full device_urls (e.g., "io://gw/123#1")
        
        for identifier_domain, base_device_url_from_registry in device_entry.identifiers:
            if identifier_domain == DOMAIN:
                # Check if any device URL in the coordinator's current list starts with this base_device_url
                is_still_present = any(
                    known_device_url.startswith(base_device_url_from_registry)
                    for known_device_url in coordinator.data # coordinator.data holds current devices
                )
                
                if not is_still_present:
                    # The base_device_url is no longer found in the coordinator's current devices,
                    # so it's safe to allow manual removal.
                    return True
                else:
                    # Device (or a part of it, if it's a composite device) is still present.
                    return False
        
        # Should not be reached if the device_entry has a valid Overkiz identifier.
        # Default to not allowing removal if the Overkiz identifier isn't found or logic is inconclusive.
        return False
    ```
    **Reasoning:** This function checks if the device (identified by its base URL stored in the device registry) is still present in the coordinator's current list of known devices. If not, it returns `True`, allowing Home Assistant to remove the device entry.

2.  **Implement Stale Device Cleanup on Full Refresh:**
    During initial setup and after reconnections (where a full device list is fetched), compare the devices in the registry for the config entry against the current list from the API.

    Add a helper function, for example in `homeassistant/components/overkiz/coordinator.py` (or `__init__.py`):
    ```python
    # homeassistant/components/overkiz/coordinator.py (or a similar utility location)
    
    async def _async_cleanup_stale_devices_for_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry, # Use base ConfigEntry type
        current_devices_map: dict[str, Device] # Pass coordinator.data or coordinator.devices
    ):
        """Remove stale devices from the device registry for this config entry."""
        device_registry = dr.async_get(hass)
        
        # Get all devices currently in the registry for this config entry
        registry_devices_for_entry = dr.async_entries_for_config_entry(
            device_registry, config_entry.entry_id
        )
        
        # Create a set of base_device_urls currently known to the coordinator
        current_base_urls_in_coordinator = {
            dev_url.split("#")[0] for dev_url in current_devices_map
        }

        for device_entry in registry_devices_for_entry:
            is_stale = True
            # Check if any Overkiz identifier of this device_entry is still in the coordinator's current devices
            for identifier_domain, id_value in device_entry.identifiers:
                if identifier_domain == DOMAIN:
                    if id_value in current_base_urls_in_coordinator:
                        is_stale = False
                        break # Found, not stale
            
            if is_stale:
                LOGGER.info( # Use INFO for user-impactful cleanup actions
                    "Removing stale device %s (id: %s, identifiers: %s) from registry as it is no longer provided by Overkiz config entry %s",
                    device_entry.name_by_user or device_entry.name,
                    device_entry.id,
                    device_entry.identifiers,
                    config_entry.entry_id,
                )
                device_registry.async_update_device(
                    device_id=device_entry.id,
                    remove_config_entry_id=config_entry.entry_id,
                )
    ```

    This function should be called:
    *   In `homeassistant/components/overkiz/__init__.py`, at the end of `async_setup_entry`, after `coordinator.async_config_entry_first_refresh()` has populated `coordinator.data`:
        ```python
        # In homeassistant/components/overkiz/__init__.py -> async_setup_entry
        # ...
            await coordinator.async_config_entry_first_refresh()

            # Call the cleanup function
            # Assuming _async_cleanup_stale_devices_for_entry is defined or imported
            await _async_cleanup_stale_devices_for_entry(hass, entry, coordinator.data)
        # ...
        ```
    *   In `homeassistant/components/overkiz/coordinator.py`, within `_async_update_data`'s `except (ServerDisconnectedError, NotAuthenticatedException):` block, after `self.devices = await self._get_devices()` has successfully repopulated the device list:
        ```python
        # In homeassistant/components/overkiz/coordinator.py -> _async_update_data
        # ...
                try:
                    await self.client.login()
                    self.devices = await self._get_devices() # self.devices is updated here
                    # Call the cleanup function
                    await _async_cleanup_stale_devices_for_entry(self.hass, self.config_entry, self.devices)
                except MyException as ex: # Adjust exception type as needed
        # ...
        ```
    **Reasoning:** This ensures that devices removed while HA was offline are identified and disassociated from the config entry upon startup or reconnection, using the method preferred by the rule's example.

3.  **Modify `on_device_removed` to use `async_update_device`:**
    Change the `on_device_removed` event handler in `homeassistant/components/overkiz/coordinator.py` to align with the rule's example.

    ```python
    # homeassistant/components/overkiz/coordinator.py
    @EVENT_HANDLERS.register(EventName.DEVICE_REMOVED)
    async def on_device_removed(
        coordinator: OverkizDataUpdateCoordinator, event: Event
    ) -> None:
        """Handle device removed event."""
        if not event.device_url:
            return

        base_device_url = event.device_url.split("#")[0]
        registry = dr.async_get(coordinator.hass)

        if registered_device := registry.async_get_device(
            identifiers={(DOMAIN, base_device_url)}
        ):
            LOGGER.info( # Use INFO for user-impactful cleanup actions
                "Device %s (%s) reported as removed by Overkiz API, dissociating from config entry %s",
                registered_device.name_by_user or registered_device.name,
                registered_device.id,
                coordinator.config_entry.entry_id,
            )
            # Use async_update_device with remove_config_entry_id
            registry.async_update_device(
                device_id=registered_device.id,
                remove_config_entry_id=coordinator.config_entry.entry_id,
            )

        if event.device_url in coordinator.devices: # Check before deleting
            del coordinator.devices[event.device_url]
    ```
    **Reasoning:** Using `async_update_device` with `remove_config_entry_id` is the idiomatic way for a config entry to signal it no longer provides a device. This allows Home Assistant's device registry to manage the device's lifecycle, especially for cleanup if no other config entry provides it. It also aligns directly with the rule's example implementation.

_Created at 2025-05-28 12:47:56. Prompt tokens: 87409, Output tokens: 3085, Total tokens: 99090_
