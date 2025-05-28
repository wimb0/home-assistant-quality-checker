# overkiz: dynamic-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [dynamic-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices)                                                     |
| Status | **todo**                                       |

## Overview

The `dynamic-devices` rule requires that when a new device is connected to the integration (e.g., added to the Overkiz hub), Home Assistant should automatically create the relevant entities for that device without requiring manual user intervention within Home Assistant, such as reloading the integration. The rule's example implementation suggests using a coordinator listener pattern to dynamically add entities for new devices.

The `overkiz` integration currently handles the `EventName.DEVICE_CREATED` event by triggering a full reload of its config entry. This is done in `coordinator.py` within the `on_device_created_updated` event handler:
```python
# homeassistant/components/overkiz/coordinator.py
@EVENT_HANDLERS.register(EventName.DEVICE_CREATED)
@EVENT_HANDLERS.register(EventName.DEVICE_UPDATED)
async def on_device_created_updated(
    coordinator: OverkizDataUpdateCoordinator, event: Event
) -> None:
    """Handle device unavailable / disabled event."""
    coordinator.hass.async_create_task(
        coordinator.hass.config_entries.async_reload(coordinator.config_entry.entry_id)
    )
```
While this mechanism does result in entities for the new device appearing automatically to the user, a full config entry reload is a heavier operation than the dynamic entity addition pattern shown in the rule's example. A full reload unloads and re-setups all entities for the integration, which can be disruptive if many devices are already configured.

The rule's example and the phrase "Every update `_check_device` will check if there are new devices to create entities for and add them to Home Assistant" imply a more granular approach where new devices are identified and their entities added during the coordinator's regular update cycle, without affecting existing entities.

Currently, the platform setup files (e.g., `sensor.py`, `cover.py`) in the `overkiz` integration add entities only once during the `async_setup_entry` call. They do not implement a listener to dynamically add entities based on coordinator updates after the initial setup, as demonstrated in the rule's example.

Therefore, while the integration meets the user-facing aspect of automatic discovery, its current implementation method (full reload for new devices) does not align with the less disruptive, more dynamic pattern advocated by the rule.

## Suggestions

To align with the `dynamic-devices` rule and its exemplified pattern, the following changes are recommended:

1.  **Modify the `DEVICE_CREATED` event handling in `coordinator.py`:**
    *   The `on_device_created_updated` handler (or a new, specific handler for `DEVICE_CREATED`) should not trigger a full config entry reload when a `DEVICE_CREATED` event occurs.
    *   Instead, it should ensure that the coordinator's internal device list (`self.devices`, which is also `self.data`) is updated to include the new device. This can be achieved by:
        *   Setting a flag within the coordinator instance (e.g., `self._needs_full_device_refresh = True`) when a `DEVICE_CREATED` event is processed.
        *   In the `_async_update_data` method, after processing all events, check this flag. If true, call `self.devices = await self._get_devices()` to refresh the complete device list from the client and then reset the flag. This ensures that `coordinator.data` provided to listeners is up-to-date.

    Example modification in `coordinator.py`:
    ```python
    # homeassistant/components/overkiz/coordinator.py

    class OverkizDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Device]]):
        # ...
        def __init__(self, ...):
            # ...
            self._new_devices_pending_refresh = False
            # ...

        async def _async_update_data(self) -> dict[str, Device]:
            # ... (fetch events) ...
            for event in events:
                LOGGER.debug(event)

                if event.name == EventName.DEVICE_CREATED:
                    # Mark that a full device list refresh is needed after processing events
                    self._new_devices_pending_refresh = True
                    # Avoid reloading the config entry for DEVICE_CREATED
                    # Potentially, DEVICE_UPDATED might still trigger a reload if complex changes occur
                    # or could be handled by a separate, more specific handler.
                    # For this rule, we focus on DEVICE_CREATED.
                    # If on_device_created_updated is kept shared, it needs logic:
                    # if event.name == EventName.DEVICE_UPDATED:
                    #     self.hass.async_create_task(
                    #         self.hass.config_entries.async_reload(self.config_entry.entry_id)
                    #     )
                    # else: # It's DEVICE_CREATED
                    #     self._new_devices_pending_refresh = True
                    # continue # Skip generic handler if it reloads for DEVICE_CREATED

                elif event_handler := EVENT_HANDLERS.get(event.name):
                    # Ensure the generic handler for DEVICE_CREATED (if it reloads) is not called,
                    # or modify that handler.
                    if event.name == EventName.DEVICE_CREATED and event_handler == on_device_created_updated:
                         pass # Already handled above for dynamic addition
                    else:
                        await event_handler(self, event)
            
            if self._new_devices_pending_refresh:
                LOGGER.debug("New device(s) created, refreshing full device list.")
                self.devices = await self._get_devices()
                self._new_devices_pending_refresh = False
            # ...
            return self.devices

    # And remove/modify the existing on_device_created_updated handler's reload for DEVICE_CREATED:
    @EVENT_HANDLERS.register(EventName.DEVICE_CREATED) # Or handle within _async_update_data directly
    async def on_device_created(
        coordinator: OverkizDataUpdateCoordinator, event: Event
    ) -> None:
        """Handle device created event for dynamic addition."""
        # This handler might set a flag as shown above in _async_update_data,
        # or directly add the device to coordinator.devices if event contains full data
        # and a full refresh in _async_update_data isn't strictly needed.
        # For now, flagging for refresh in _async_update_data is safer.
        coordinator._new_devices_pending_refresh = True # Example of how a dedicated handler could work

    @EVENT_HANDLERS.register(EventName.DEVICE_UPDATED)
    async def on_device_updated( # Separated from DEVICE_CREATED
        coordinator: OverkizDataUpdateCoordinator, event: Event
    ) -> None:
        """Handle device updated event."""
        # DEVICE_UPDATED might still warrant a reload for complex changes,
        # or could be made more granular in the future.
        coordinator.hass.async_create_task(
            coordinator.hass.config_entries.async_reload(coordinator.config_entry.entry_id)
        )
    ```
    *(Note: The above is a conceptual sketch. The exact changes to event handlers need careful implementation to ensure `DEVICE_UPDATED` logic (if it must reload) is preserved or also improved, while `DEVICE_CREATED` avoids the reload.)*

2.  **Implement the listener pattern in platform setup files:**
    For each platform (e.g., `sensor.py`, `cover.py`, `light.py`, etc.):
    *   In `async_setup_entry`, initialize a `known_devices` set (e.g., `set[str]` to store device URLs for which entities have been created on that platform).
    *   Create a callback function (e.g., `_async_add_new_entities_listener`). This function will:
        *   Iterate through `coordinator.data.values()` (or `data.platforms[current_platform]` if already filtered).
        *   Identify devices that are new (i.e., their URL is not in `known_devices`) and are relevant to the current platform.
        *   If new devices are found:
            *   Create the necessary entity/entities for each new device.
            *   Call `async_add_entities` with these new entities.
            *   Add the new device URLs to the `known_devices` set.
    *   Call this callback function once at the end of `async_setup_entry` to process initially available devices.
    *   Register this callback as a listener to the coordinator using `entry.async_on_unload(coordinator.async_add_listener(_async_add_new_entities_listener))`.

    Example for `sensor.py` (structure based on rule example):
    ```python
    # homeassistant/components/overkiz/sensor.py
    # ... other imports ...
    from homeassistant.core import callback # Add this

    async def async_setup_entry(
        hass: HomeAssistant,
        entry: OverkizDataConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up the Overkiz sensors from a config entry."""
        data = entry.runtime_data
        coordinator = data.coordinator # Get coordinator

        known_device_urls: set[str] = set()

        @callback
        def _async_add_new_sensor_entities() -> None:
            """Check for new devices and add their sensor entities."""
            new_entities: list[SensorEntity] = []
            
            current_devices_for_platform = [
                device for device in coordinator.data.values() 
                # Optional: if platforms dict is still useful, filter here
                # This example iterates all and checks conditions inside
            ]

            for device in current_devices_for_platform:
                if device.device_url in known_device_urls:
                    continue

                # Logic from current sensor.py to determine if/which sensors to create for this device
                # Example for HomeKitSetupCodeSensor
                if device.widget == UIWidget.HOMEKIT_STACK:
                    new_entities.append(
                        OverkizHomeKitSetupCodeSensor(device.device_url, coordinator)
                    )
                
                # Example for OverkizStateSensor
                if not (device.widget in IGNORED_OVERKIZ_DEVICES or device.ui_class in IGNORED_OVERKIZ_DEVICES):
                    for state in device.definition.states:
                        if (description := SUPPORTED_STATES.get(state.qualified_name)):
                            new_entities.append(
                                OverkizStateSensor(device.device_url, coordinator, description)
                            )
                
                # If any entity was identified for this device, mark it as known for this platform
                # A more robust way might be to check if new_entities got anything for THIS device_url
                # before adding to known_device_urls. For simplicity here, if we check a device,
                # we consider it "processed" for newness.
                # This logic needs to be careful not to re-add if an entity for it already exists.
                # The check `device.device_url in known_device_urls` handles not reprocessing.
                # The key is adding to known_device_urls *after* entities are queued for creation.

            if new_entities:
                async_add_entities(new_entities)
                # Update known_device_urls with devices for which entities were actually added
                for entity in new_entities:
                    # Assuming entity.device_url is the primary device_url
                    if hasattr(entity, 'device_url'):
                         known_device_urls.add(entity.device_url)


        # Call once for initial setup
        _async_add_new_sensor_entities()

        # Register as a listener to handle devices added later
        entry.async_on_unload(
            coordinator.async_add_listener(_async_add_new_sensor_entities)
        )
    ```
    This pattern would need to be adapted and implemented for each relevant platform (`cover.py`, `light.py`, etc.).

By making these changes, the `overkiz` integration would add entities for newly discovered devices dynamically and less disruptively, aligning better with the `dynamic-devices` rule's intent and example.

_Created at 2025-05-28 12:32:38. Prompt tokens: 87140, Output tokens: 2912, Total tokens: 98920_
