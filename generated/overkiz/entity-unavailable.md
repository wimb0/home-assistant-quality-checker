# overkiz: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **done**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `entity-unavailable` rule states that if an integration can't fetch data from a device or service, it should mark its entities as unavailable. If data can be fetched successfully but a few pieces of data are missing for an entity, that entity's state should be marked as unknown. The rule applies to the `overkiz` integration as it polls data from an external service/hub using a `DataUpdateCoordinator`.

The `overkiz` integration correctly follows this rule for its entities derived from `OverkizEntity` (which includes the vast majority of its platforms like sensors, switches, covers, lights, climate, etc.).

1.  **Coordinator-level failures:**
    The `OverkizDataUpdateCoordinator` in `coordinator.py` handles API communication. Its `_async_update_data` method catches various exceptions (e.g., `BadCredentialsException`, `TooManyRequestsException`, `TimeoutError`, `ClientError`).
    *   If critical exceptions like `BadCredentialsException` occur, it raises `ConfigEntryAuthFailed`.
    *   For other communication failures (e.g., `TimeoutError`, `TooManyRequestsException`), it raises `UpdateFailed`.
    Both `ConfigEntryAuthFailed` and `UpdateFailed` will cause the `CoordinatorEntity.last_update_success` flag to be `False`.
    The base `OverkizEntity` (in `entity.py`) from which most Overkiz entities inherit, defines its availability as:
    ```python
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.available and super().available
    ```
    Here, `super().available` (from `CoordinatorEntity`) will return `False` if `self.coordinator.last_update_success` is `False`. This correctly marks all associated entities as unavailable when the coordinator cannot fetch data from the Overkiz service.

2.  **Individual device-level unavailability:**
    The `OverkizEntity.available` property also checks `self.device.available`.
    *   The `pyoverkiz.models.Device` object (referenced by `self.device`) has an `available` attribute.
    *   The `OverkizDataUpdateCoordinator` listens to events from the Overkiz API. Event handlers like `on_device_unavailable_disabled` (in `coordinator.py`) update `coordinator.devices[event.device_url].available = False`.
    *   Thus, if the Overkiz API reports a specific device as unavailable or disabled, `self.device.available` becomes `False`, and the corresponding Home Assistant entity becomes unavailable, even if the coordinator successfully fetched events for other devices. This aligns with the rule's example: `super().available and self.identifier in self.coordinator.data`. If a device is explicitly marked as unavailable by the API, it's equivalent to its data being effectively missing or invalid.

3.  **Device removal:**
    If a device is removed entirely from the Overkiz hub, the `on_device_removed` event handler in `coordinator.py` will delete it from `coordinator.devices`.
    When an entity associated with this removed device attempts to access `self.device` (e.g., in its `available` property or other state properties via `self.coordinator.data[self.device_url]`), a `KeyError` will be raised.
    Home Assistant's core entity update mechanism catches such exceptions during state updates and automatically sets `_attr_available = False` for the entity, effectively marking it unavailable. This achieves the same outcome as the rule's example check `self.identifier in self.coordinator.data`.

4.  **Missing pieces of data (state unknown):**
    If a device is available and the coordinator update is successful, but a specific state value for an entity is missing (e.g., a particular sensor reading is not provided by the API for that device), the entity properties (like `native_value` in `OverkizStateSensor`) are designed to return `None`. Home Assistant typically interprets a `None` state for a sensor as "unknown". This correctly implements the part of the rule about marking the *state* as unknown when individual pieces of data are missing, while the entity itself can remain available. For example, in `sensor.py`, `OverkizStateSensor.native_value`:
    ```python
    @property
    def native_value(self) -> StateType:
        # ...
        if (
            state is None
            or state.value is None
            # ...
        ):
            return None # Results in an "unknown" state for the sensor
        # ...
        return state.value
    ```

The `OverkizScene` entities are not derived from `CoordinatorEntity` and manage their availability differently, primarily tied to the overall config entry health. However, the rule's examples focus on entities with polled states or `async_update`, which scenes typically do not have. For all other stateful entities managed by the coordinator, the `overkiz` integration adheres to the `entity-unavailable` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:20:46. Prompt tokens: 87242, Output tokens: 1255, Total tokens: 95575_
