# nest: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `log-when-unavailable` rule requires that integrations log a message at `INFO` level once when a device or service becomes unavailable, and once when it becomes available again. This helps users diagnose connectivity issues.

The `nest` integration interacts with the Google Nest cloud service (Smart Device Management API) and manages individual Nest devices (thermostats, cameras, etc.). Both the service and the individual devices can become unavailable. Therefore, the rule applies to this integration.

The integration currently does **NOT** fully follow this rule for the following reasons:

1.  **Device-Specific Unavailability:**
    *   Entities such as sensors (`sensor.py:SensorBase`), climate devices (`climate.py:ThermostatEntity`), and event entities (`event.py:NestTraitEventEntity`) derive their availability status from `NestDeviceInfo`, which checks the `ConnectivityTrait` of the physical device.
    *   When a device's `ConnectivityTrait` indicates it's "OFFLINE", `NestDeviceInfo.available` returns `False`, and the corresponding Home Assistant entity becomes unavailable.
    *   However, these entities **do not implement the required logging pattern**. They do not use an instance variable (e.g., `_unavailable_logged`) to track the logged state and therefore do not log messages like "Device X is unavailable" or "Device X is back online" at `INFO` level when their availability changes. This is missing from `SensorBase`, `ThermostatEntity`, and `NestTraitEventEntity`.
    *   For camera entities (`camera.py:NestCameraBaseEntity` and its subclasses):
        *   `NestRTSPEntity` currently hardcodes its `available` property to `True` (see `camera.py`) due to stream flakiness. While this is a separate issue (potentially for `entity-unavailable`), it means that for device connectivity changes reported by `ConnectivityTrait`, it won't log unavailability.
        *   Stream-specific errors in camera entities are handled (e.g., logging at `DEBUG` or raising `HomeAssistantError`), but this is not the same as the "log once at INFO" pattern for general availability state changes.
        *   `NestCameraBaseEntity` itself does not define an `available` property based on `NestDeviceInfo` and thus defaults to always available unless overridden by subclasses.

2.  **Service-Level Unavailability (Connection to Google SDM API):**
    *   The `nest` integration relies on the `google-nest-sdm` library for communication with the Google SDM API via a Pub/Sub subscriber.
    *   If the connection to the Google service is lost (e.g., internet outage, Google API issues), the `google-nest-sdm` library has its own internal logging (e.g., `_LOG.error("Error listening for pubsub messages: ...")`, `_LOG.info("Subscriber reconnected")`).
    *   However, the Home Assistant `nest` integration code itself (within `homeassistant/components/nest/`) does not have an explicit mechanism to detect these overall service connection state changes from the subscriber and log them with the "log once at `INFO` level" pattern. The rule implies the *integration* should ensure this logging. While the underlying library logs are helpful and are exposed via the `loggers` entry in `manifest.json`, they may not strictly adhere to the "log once when unavailable, log once when reconnected at INFO level from the integration's perspective" requirement (e.g., multiple error logs before a successful reconnect). The integration does not use a `DataUpdateCoordinator` for the main subscriber connection, where `UpdateFailed` would trigger HA's built-in coordinator logging for this.

## Suggestions

To make the `nest` integration compliant with the `log-when-unavailable` rule:

1.  **Implement Device-Specific Unavailability Logging for Entities:**

    For entities that reflect the online/offline status of a physical Nest device (sensors, climate, events), implement the logging pattern. This typically involves:
    *   Adding an instance variable `_unavailable_logged: bool = False` to the entity class.
    *   Overriding the `async_update_ha_state` method to check for changes in availability and log accordingly.

    **Example for `SensorBase` in `homeassistant/components/nest/sensor.py` (and similarly for `ThermostatEntity`, `NestTraitEventEntity`):**

    ```python
    # homeassistant/components/nest/sensor.py

    # ... import _LOGGER from appropriate module, likely:
    # from . import _LOGGER (if _LOGGER is defined in __init__.py and represents the integration logger)
    # or directly:
    # import logging
    # _LOGGER = logging.getLogger(__name__) # If entities log to their own module's logger

    class SensorBase(SensorEntity):
        _attr_should_poll = False
        _attr_state_class = SensorStateClass.MEASUREMENT
        _attr_has_entity_name = True
        _unavailable_logged: bool = False # Add this line

        def __init__(self, device: Device) -> None:
            """Initialize the sensor."""
            self._device = device
            self._device_info = NestDeviceInfo(device)
            # Initialize _attr_available based on current device status
            # This helps set the initial state for comparison in async_update_ha_state
            self._attr_available = self._device_info.available # Add this line
            self._attr_unique_id = f"{device.name}-{self.device_class}"
            self._attr_device_info = self._device_info.device_info

        @property
        def available(self) -> bool:
            """Return the device availability."""
            # This property will be used by the base class during state updates
            return self._device_info.available

        async def async_added_to_hass(self) -> None:
            """Run when entity is added to register update signal handler."""
            self.async_on_remove(
                self._device.add_update_listener(self.async_write_ha_state)
            )

        async def async_update_ha_state(self, force_refresh: bool = False) -> None:
            """Update Home Assistant with current state and log availability changes."""
            # Store the availability state as Home Assistant knew it before this update.
            # self.available reflects the new state from the device for this update cycle.
            previous_ha_state_available = self._attr_available
            current_device_info_available = self._device_info.available

            # Let the superclass handle the regular state update.
            # This will update self._attr_available based on the @property available.
            await super().async_update_ha_state(force_refresh)

            # Now, self._attr_available holds the new availability state.
            # Compare with previous_ha_state_available to detect a change.

            if current_device_info_available == previous_ha_state_available and previous_ha_state_available is not None:
                # No change in availability status, no logging needed for availability.
                return

            if not current_device_info_available: # Device is now unavailable
                if not self._unavailable_logged:
                    # Log only if it just became unavailable or was already unavailable but not yet logged.
                    # This condition ensures it logs if previous_ha_state_available was True or None (initial).
                    _LOGGER.info("%s is unavailable", self.entity_id)
                    self._unavailable_logged = True
            else: # Device is now available (current_device_info_available is True)
                if self._unavailable_logged:
                    _LOGGER.info("%s is back online", self.entity_id)
                    self._unavailable_logged = False
                elif previous_ha_state_available is None and not self._unavailable_logged:
                    # Handles initial setup where device is immediately available.
                    # Ensure _unavailable_logged is False, no "back online" log needed.
                    self._unavailable_logged = False
    ```

    *   This pattern should be applied to:
        *   `homeassistant/components/nest/sensor.py::SensorBase`
        *   `homeassistant/components/nest/climate.py::ThermostatEntity`
        *   `homeassistant/components/nest/event.py::NestTraitEventEntity` (if it's intended to reflect device availability).
    *   **For Camera Entities:**
        *   Consider if `NestCameraBaseEntity` should also adopt `NestDeviceInfo.available` for its `available` property. If so, the same logging logic would apply.
        *   If `NestRTSPEntity.available` remains hardcoded to `True`, this specific logging for device connectivity won't apply to it. However, if stream-specific issues were to make it unavailable (and `_attr_available` was set to `False`), similar logging for stream unavailability/restoration would be beneficial.

2.  **Address Service-Level Unavailability Logging:**

    This is more complex due to the push-based subscriber model.
    *   **Option 1 (Ideal but potentially requires library changes):** The `google-nest-sdm` library's `GoogleNestSubscriber` could expose distinct connection status events/callbacks (e.g., `on_disconnected`, `on_connected`). The HA `nest` integration (`__init__.py`) could then listen to these and implement the "log once at `INFO` level" logic using a flag similar to `_unavailable_logged`.
        ```python
        # Hypothetical snippet in homeassistant/components/nest/__init__.py
        # This assumes the subscriber calls these methods appropriately.

        _subscriber_unavailable_logged = False

        def _handle_subscriber_disconnected(reason: str):
            nonlocal _subscriber_unavailable_logged
            if not _subscriber_unavailable_logged:
                _LOGGER.info("Connection to Nest service lost: %s", reason)
                _subscriber_unavailable_logged = True

        def _handle_subscriber_connected():
            nonlocal _subscriber_unavailable_logged
            if _subscriber_unavailable_logged:
                _LOGGER.info("Connection to Nest service restored.")
                _subscriber_unavailable_logged = False
            # On initial successful connection, ensure flag is clear.
            elif not _subscriber_unavailable_logged: # First connection
                 _subscriber_unavailable_logged = False


        # In async_setup_entry, after subscriber is initialized:
        # subscriber.set_connection_callbacks(on_connected=_handle_subscriber_connected,
        #                                     on_disconnected=_handle_subscriber_disconnected)
        ```
    *   **Option 2 (Review existing library logs):** Thoroughly review the logs produced by `google-nest-sdm` (logger `google_nest_sdm`) during connection loss and restoration. If they already perfectly match the "once at INFO level when unavailable, once at INFO level when reconnected" pattern, it might be argued as sufficient, though the rule generally implies the integration itself takes responsibility. If logs are too verbose, at different levels, or don't clearly delineate the "once" aspect, then Option 1 or custom monitoring within the HA integration would be better.

Implementing the device-specific unavailability logging (Suggestion 1) is the most straightforward first step and directly addresses a clear gap in multiple entity types. Addressing service-level logging (Suggestion 2) might require more architectural considerations or coordination with the `google-nest-sdm` library maintainers.

_Created at 2025-05-28 22:59:12. Prompt tokens: 32651, Output tokens: 2677, Total tokens: 43469_
