# nest: dynamic-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [dynamic-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices)                                                     |
| Status | **todo**                                       |

## Overview

The `dynamic-devices` rule requires that integrations automatically discover and add entities for new devices that are connected after the initial setup, without requiring a manual reload of the integration.

This rule **applies** to the `nest` integration because users can add new Nest devices (cameras, thermostats, doorbells, etc.) to their Google account at any time, and these should be reflected in Home Assistant automatically.

The `nest` integration currently does **not** follow this rule. When the underlying `google-nest-sdm` library signals a change in device structure (a "relation update" event via the Pub/Sub stream), the integration logs a message indicating that a reload is needed to see these changes. It does not automatically identify new devices and create their corresponding Home Assistant entities.

Specifically, in `homeassistant/components/nest/__init__.py`, the `SignalUpdateCallback.async_handle_event` method handles incoming messages from the Nest Pub/Sub subscription:

```python
# homeassistant/components/nest/__init__.py
# class SignalUpdateCallback:
# ...
    async def async_handle_event(self, event_message: EventMessage) -> None:
        """Process an incoming EventMessage."""
        if event_message.relation_update:
            _LOGGER.info("Devices or homes have changed; Need reload to take effect")
            return  # <--- Returns here, no dynamic device addition occurs
        # ... rest of the method handles events for existing devices
```
When `event_message.relation_update` is true, the method logs the need for a reload and then returns. The platform setup functions (e.g., `camera.async_setup_entry`, `sensor.async_setup_entry`) are only called during the initial loading of the integration or after a manual reload. They iterate through the devices known at that point and do not have a mechanism to add entities for devices that appear later.

## Suggestions

To make the `nest` integration compliant with the `dynamic-devices` rule, the following changes are recommended:

1.  **Refresh Device Manager on Relation Update:**
    When a `relation_update` event is received in `SignalUpdateCallback.async_handle_event`, the integration should first ensure its `DeviceManager` instance is up-to-date. This might involve re-fetching the device manager from the `google-nest-sdm` library:
    ```python
    # In homeassistant/components/nest/__init__.py
    # Inside SignalUpdateCallback.async_handle_event:
    if event_message.relation_update:
        _LOGGER.info("Device relations updated. Refreshing device manager and dispatching discovery.")
        try:
            # Assuming self._config_entry is the NestConfigEntry and it holds runtime_data
            subscriber = self._config_entry.runtime_data.subscriber
            new_device_manager = await subscriber.async_get_device_manager()
            self._config_entry.runtime_data.device_manager = new_device_manager
        except ApiException as err:
            _LOGGER.error(f"Failed to refresh device manager after relation update: {err}")
            return # Avoid dispatching if device manager refresh fails

        # Dispatch a signal that platforms can listen to
        async_dispatcher_send(self._hass, f"nest_discover_new_devices_{self._config_entry.entry_id}")
        return
    ```

2.  **Implement Per-Platform Dynamic Entity Addition:**
    Each platform (camera, climate, sensor, event) should listen for the dispatched signal and add entities for any new devices relevant to that platform. This involves:
    *   Storing its `async_add_entities` callback received during `async_setup_entry`.
    *   Maintaining a set of known device IDs for which it has already created entities.
    *   Upon receiving the discovery signal, iterating through all devices in the (updated) `DeviceManager`, identifying new devices, creating entities for them, and adding them using the stored `async_add_entities` callback.

    **Example for `sensor.py`:**
    ```python
    # homeassistant/components/nest/sensor.py
    from homeassistant.core import HomeAssistant, callback
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    # ... other imports ...
    from google_nest_sdm.device_traits import TemperatureTrait, HumidityTrait # Ensure these are imported

    async def async_setup_entry(
        hass: HomeAssistant,
        entry: NestConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up the sensors."""
        device_manager = entry.runtime_data.device_manager
        
        # Store known devices for this platform to avoid duplicates
        known_sensor_device_ids: set[str] = set()

        @callback
        def _discover_new_sensor_entities() -> None:
            """Discover and add new sensor entities."""
            new_entities_to_add = []
            # Iterate over all devices from the potentially updated device_manager
            for device_id, device in device_manager.devices.items():
                if device_id in known_sensor_device_ids:
                    continue

                device_sensors = []
                if TemperatureTrait.NAME in device.traits:
                    device_sensors.append(TemperatureSensor(device))
                if HumidityTrait.NAME in device.traits:
                    device_sensors.append(HumiditySensor(device))
                
                if device_sensors:
                    _LOGGER.info(f"Adding new sensor entities for Nest device: {device_id}")
                    new_entities_to_add.extend(device_sensors)
                    known_sensor_device_ids.add(device_id)
            
            if new_entities_to_add:
                async_add_entities(new_entities_to_add)

        # Initial discovery and entity creation
        _discover_new_sensor_entities()

        # Listen for discovery signals triggered by relation_update
        entry.async_on_unload(
            async_dispatcher_connect(
                hass,
                f"nest_discover_new_devices_{entry.entry_id}",
                _discover_new_sensor_entities,
            )
        )
    ```
    This pattern should be replicated in `camera.py`, `climate.py`, and `event.py`, each tailored to the specific entities and traits relevant to that platform.

**Why these changes satisfy the rule:**
By implementing these suggestions:
*   The integration will actively look for new devices when the Nest API signals a change in the device structure (`relation_update`).
*   New devices will have their entities (sensors, cameras, etc.) automatically created and added to Home Assistant without requiring a manual restart or reload of the integration.
*   Each platform will manage its own entities, using the `async_add_entities` callback provided to it at setup, which is the standard Home Assistant pattern.

This makes the user experience better, as newly added Nest devices will appear in Home Assistant automatically after they are configured in the Nest/Google Home app.

_Created at 2025-05-28 23:07:24. Prompt tokens: 32500, Output tokens: 1675, Total tokens: 42539_
