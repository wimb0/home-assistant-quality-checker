# nest: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unavailable` rule applies to the `nest` integration because it interacts with cloud services and physical devices (cameras, thermostats, doorbells) that can become unreachable or report an offline status. The integration must accurately reflect this unavailability in its entities.

The integration partially follows the rule:
*   **Sensor entities** (e.g., `TemperatureSensor`, `HumiditySensor` in `sensor.py`) and **Climate entities** (`ThermostatEntity` in `climate.py`) correctly implement the `available` property. They utilize `NestDeviceInfo`, which checks the `ConnectivityTrait` of the device. If the trait reports "OFFLINE", `NestDeviceInfo.available` returns `False`, and consequently, these entities correctly report themselves as unavailable. They also register an update listener (`_device.add_update_listener(self.async_write_ha_state)`) to react to changes in device state.

However, the integration does NOT fully follow the rule for other entity types:
*   **Camera entities**:
    *   `NestRTSPEntity` in `camera.py` explicitly overrides the `available` property to always `return True`. The comment within this property indicates this is a workaround for flaky streams, but it violates the rule by not reflecting the device's "OFFLINE" status from `ConnectivityTrait`.
        ```python
        # homeassistant/components/nest/camera.py
        class NestRTSPEntity(NestCameraBaseEntity):
            # ...
            @property
            def available(self) -> bool:
                """Return True if entity is available."""
                # ... (comment about flaky streams) ...
                return True # This ignores device offline status
        ```
    *   `NestWebRTCEntity` in `camera.py` inherits from `NestCameraBaseEntity`. The base class `NestCameraBaseEntity` currently does not implement an `available` property that checks `NestDeviceInfo`. Thus, `NestWebRTCEntity` defaults to `Camera.available` which is `True`, irrespective of the device's actual connectivity status.
*   **Event entities** (`NestTraitEventEntity` in `event.py`):
    *   This entity does not override the `available` property. It defaults to `EventEntity.available` which is `True`. It does not use `NestDeviceInfo` to determine its availability based on the device's `ConnectivityTrait`.
        ```python
        # homeassistant/components/nest/event.py
        class NestTraitEventEntity(EventEntity):
            # ...
            # No 'available' property defined, defaults to True.
            # NestDeviceInfo is instantiated for _attr_device_info, but not used for availability.
        ```
    *   Additionally, `NestTraitEventEntity` uses `_device.add_event_callback(self._async_handle_event)`. While this handles specific Nest events, it may not trigger updates for general device state changes like connectivity. To properly update availability, it should also listen to general device trait updates using `_device.add_update_listener`.

Because Camera and Event entities do not correctly mark themselves as unavailable when the underlying device is offline, the integration is "todo" for this rule.

## Suggestions

To make the `nest` integration compliant with the `entity-unavailable` rule, the following changes are recommended:

1.  **Modify `NestCameraBaseEntity` in `homeassistant/components/nest/camera.py`:**
    *   Store an instance of `NestDeviceInfo`.
    *   Implement the `available` property to use `NestDeviceInfo.available`.
    *   Ensure `_attr_brand` and `_attr_model` also use the `_nest_device_info` instance for consistency if they rely on its methods/properties (though `NestDeviceInfo` provides them as direct properties of the device itself, the current implementation is fine, but storing `_nest_device_info` is key).

    ```python
    # homeassistant/components/nest/camera.py
    from .device_info import NestDeviceInfo # Ensure NestDeviceInfo is imported

    class NestCameraBaseEntity(Camera, ABC):
        _attr_has_entity_name = True
        _attr_name = None
        _attr_is_streaming = True
        _attr_supported_features = CameraEntityFeature.STREAM
        _nest_device_info: NestDeviceInfo # Add for type hinting and clarity

        def __init__(self, device: Device) -> None:
            super().__init__()
            self._device = device
            self._nest_device_info = NestDeviceInfo(device) # Store the instance
            self._attr_device_info = self._nest_device_info.device_info
            self._attr_brand = self._nest_device_info.device_brand
            self._attr_model = self._nest_device_info.device_model
            self.stream_options[CONF_EXTRA_PART_WAIT_TIME] = 3
            self._attr_unique_id = f"{self._device.name}-camera"

        @property
        def available(self) -> bool:
            """Return True if entity is available."""
            return self._nest_device_info.available

        async def async_added_to_hass(self) -> None:
            """Run when entity is added to register update signal handler."""
            # This already correctly uses add_update_listener
            self.async_on_remove(
                self._device.add_update_listener(self.async_write_ha_state)
            )
    ```

2.  **Modify `NestRTSPEntity` in `homeassistant/components/nest/camera.py`:**
    *   Remove the overridden `available` property. This will allow it to inherit the correct availability logic from the modified `NestCameraBaseEntity`. The flakiness of streams should be handled by other means (e.g., `stream_source` returning `None` or `is_streaming` property) rather than overriding the fundamental device availability.

    ```python
    # homeassistant/components/nest/camera.py
    class NestRTSPEntity(NestCameraBaseEntity):
        _rtsp_stream: RtspStream | None = None
        _rtsp_live_stream_trait: CameraLiveStreamTrait

        def __init__(self, device: Device) -> None:
            """Initialize the camera."""
            super().__init__(device)
            self._create_stream_url_lock = asyncio.Lock()
            self._rtsp_live_stream_trait = device.traits[CameraLiveStreamTrait.NAME]
            self._refresh_unsub: Callable[[], None] | None = None

        @property
        def use_stream_for_stills(self) -> bool:
            """Always use the RTSP stream to generate snapshots."""
            return True

        # REMOVE THE FOLLOWING PROPERTY:
        # @property
        # def available(self) -> bool:
        #     """Return True if entity is available."""
        #     # ...
        #     return True

        # ... (rest of the class)
    ```
    (`NestWebRTCEntity` will automatically benefit from the base class change as it doesn't override `available`.)

3.  **Modify `NestTraitEventEntity` in `homeassistant/components/nest/event.py`:**
    *   Store an instance of `NestDeviceInfo`.
    *   Implement the `available` property to use `NestDeviceInfo.available`.
    *   In `async_added_to_hass`, add `_device.add_update_listener(self.async_write_ha_state)` to ensure the entity reacts to general device state updates, including connectivity changes.

    ```python
    # homeassistant/components/nest/event.py
    from .device_info import NestDeviceInfo # Ensure NestDeviceInfo is imported

    class NestTraitEventEntity(EventEntity):
        entity_description: NestEventEntityDescription
        _attr_has_entity_name = True
        _nest_device_info: NestDeviceInfo # Add for type hinting and clarity

        def __init__(
            self, entity_description: NestEventEntityDescription, device: Device
        ) -> None:
            super().__init__() # Call super() first
            self.entity_description = entity_description
            self._device = device
            self._nest_device_info = NestDeviceInfo(device) # Store the instance
            self._attr_unique_id = f"{device.name}-{entity_description.key}"
            self._attr_device_info = self._nest_device_info.device_info # Use the stored instance

        @property
        def available(self) -> bool:
            """Return True if entity is available."""
            return self._nest_device_info.available

        async def _async_handle_event(self, event_message: EventMessage) -> None:
            """Handle a device event."""
            if (
                event_message.relation_update
                or not event_message.resource_update_name
                or not (events := event_message.resource_update_events)
            ):
                return
            last_nest_event_id = self.state_attributes.get("nest_event_id")
            for api_event_type, nest_event in events.items():
                if api_event_type not in self.entity_description.api_event_types:
                    continue

                event_type = EVENT_NAME_MAP[api_event_type]
                nest_event_id = nest_event.event_token
                if last_nest_event_id is not None and last_nest_event_id == nest_event_id:
                    return

                self._trigger_event(
                    event_type,
                    {"nest_event_id": nest_event_id},
                )
                self.async_write_ha_state()
                return

        async def async_added_to_hass(self) -> None:
            """Run when entity is added to attach an event listener."""
            # For specific Nest events handled by this entity
            self.async_on_remove(self._device.add_event_callback(self._async_handle_event))
            # For general device trait updates, including connectivity, to update availability
            self.async_on_remove(
                self._device.add_update_listener(self.async_write_ha_state)
            )
    ```

These changes will ensure that all Nest entities consistently use the `ConnectivityTrait` (via `NestDeviceInfo`) to determine their availability, aligning the integration with the `entity-unavailable` rule.

_Created at 2025-05-28 22:57:02. Prompt tokens: 32602, Output tokens: 2478, Total tokens: 41647_
