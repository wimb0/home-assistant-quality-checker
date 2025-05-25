```markdown
# fritzbox: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **done**                                       |

## Overview

The `entity-unavailable` rule requires that entities are marked as unavailable when the integration cannot fetch data from the device or service they represent. This integration connects to a FRITZ!Box to control and monitor Smart Home devices. The rule is applicable as the availability of entities directly depends on the communication with the FRITZ!Box and the status of the connected devices.

The `fritzbox` integration uses a `DataUpdateCoordinator` (`FritzboxDataUpdateCoordinator` defined in `coordinator.py`) to handle fetching data from the FRITZ!Box via the `pyfritzhome` library. Entities (`FritzBoxDeviceEntity` and `FritzBoxEntity` defined in `entity.py`) inherit from `CoordinatorEntity`, which provides built-in availability logic based on the coordinator's update status.

Specifically, the `FritzboxDataUpdateCoordinator._async_update_data` method (in `coordinator.py`) handles communication errors:
- It catches `requests.exceptions.RequestConnectionError` and raises `homeassistant.helpers.update_coordinator.UpdateFailed`. This is the standard mechanism for a coordinator to signal that an update failed due to a connection issue. When the coordinator raises `UpdateFailed`, all associated `CoordinatorEntity` instances automatically become unavailable.
- It handles `requests.exceptions.HTTPError` by attempting to log in again, and if that fails with `pyfritzhome.LoginError`, it raises `homeassistant.exceptions.ConfigEntryAuthFailed`, which correctly triggers a reauthentication flow rather than just marking entities unavailable for a persistent authentication issue.

Furthermore, the base class for most entities, `FritzBoxDeviceEntity` (in `entity.py`), overrides the `available` property:
```python
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.data.present
```
This implementation correctly combines the availability state provided by the base `CoordinatorEntity` (which reflects the coordinator's status and thus connection health) with the `present` attribute of the device object fetched from the FRITZ!Box (`self.data.present`). This ensures that an entity is marked unavailable if either the connection to the FRITZ!Box is lost *or* if the FRITZ!Box reports that the specific device is not currently present.

Additionally, the `FritzboxDataUpdateCoordinator._update_fritz_devices` method includes specific logic to mark certain power meter devices with zero readings as `device.present = False`. This provides an extra layer of availability accuracy based on device data heuristics, which then also feeds into the `FritzBoxDeviceEntity.available` logic.

The entity types (`binary_sensor.py`, `cover.py`, `light.py`, `sensor.py`, `switch.py`, `climate.py`) all inherit from `FritzBoxDeviceEntity` (or `FritzBoxEntity` for buttons/templates which don't have a 'present' state), benefiting from this well-implemented availability logic.

Based on the use of a coordinator that correctly signals update failures and entities that combine this with device-specific presence checks, the integration fully follows the `entity-unavailable` rule.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:34:35. Prompt tokens: 19233, Output tokens: 800, Total tokens: 21040_
