# wled: devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/devices)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `devices` rule mandates that integrations create device entries in the Home Assistant device registry for physical devices or services they represent. This is crucial for user experience, as it groups related entities and provides a central place for device information. The rule emphasizes that this device information should be as complete as possible.

This rule applies to the `wled` integration, as it represents physical WLED lighting devices.

The `wled` integration fully follows this rule. It achieves this through a base entity class, `WLEDEntity`, defined in `entity.py`. All specific WLED entities (lights, sensors, switches, etc.) inherit from this base class.

The `WLEDEntity` class includes a `device_info` property that constructs and returns a `DeviceInfo` object:

```python
# entity.py
class WLEDEntity(CoordinatorEntity[WLEDDataUpdateCoordinator]):
    """Defines a base WLED entity."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this WLED device."""
        return DeviceInfo(
            connections={
                (CONNECTION_NETWORK_MAC, self.coordinator.data.info.mac_address)
            },
            identifiers={(DOMAIN, self.coordinator.data.info.mac_address)},
            name=self.coordinator.data.info.name,
            manufacturer=self.coordinator.data.info.brand,
            model=self.coordinator.data.info.product,
            sw_version=str(self.coordinator.data.info.version),
            hw_version=self.coordinator.data.info.architecture,
            configuration_url=f"http://{self.coordinator.wled.host}",
        )
```

This implementation ensures that each entity associated with a WLED device is correctly linked to a device entry in the registry. The `DeviceInfo` object is populated with comprehensive information sourced directly from the WLED device's data (via `self.coordinator.data.info`):
*   **`connections`**: Uses the device's MAC address (`self.coordinator.data.info.mac_address`) with `CONNECTION_NETWORK_MAC`.
*   **`identifiers`**: Uniquely identifies the device within the `wled` domain using its MAC address.
*   **`name`**: The name of the WLED device (e.g., `self.coordinator.data.info.name`).
*   **`manufacturer`**: The brand of the WLED device (e.g., `self.coordinator.data.info.brand`).
*   **`model`**: The product name/model of the WLED device (e.g., `self.coordinator.data.info.product`).
*   **`sw_version`**: The firmware version of the WLED device (e.g., `str(self.coordinator.data.info.version)`).
*   **`hw_version`**: The hardware architecture of the WLED device (e.g., `self.coordinator.data.info.architecture`).
*   **`configuration_url`**: A direct link to the WLED device's web interface.

This set of information is robust and aligns with the rule's requirement for device information to be "as complete as possible," utilizing the data made available by the WLED device's API. All entity platforms (`light.py`, `sensor.py`, `switch.py`, `button.py`, `number.py`, `select.py`, `update.py`) define entities that inherit from `WLEDEntity`, thus consistently applying this device registration.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:57:42. Prompt tokens: 21337, Output tokens: 912, Total tokens: 25168_
