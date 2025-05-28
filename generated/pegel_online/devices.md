```markdown
# pegel_online: devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/devices)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `devices` rule requires that integrations creating entities should group those entities under devices to provide a better user experience and structure. This is applicable to the `pegel_online` integration as it creates sensor entities representing measurements from a water station.

The `pegel_online` integration fully follows this rule. It correctly defines a device for each configured water station and links the sensor entities to this device.

Specifically, the base entity class `PegelOnlineEntity` located in `homeassistant/components/pegel_online/entity.py` creates a `DeviceInfo` object in its `__init__` method:

```python
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.station.uuid)},
            name=f"{self.station.name} {self.station.water_name}",
            manufacturer=self.station.agency,
            configuration_url=self.station.base_data_url,
            entry_type=DeviceEntryType.SERVICE,
        )
```

This `DeviceInfo` object uses the `DOMAIN` and the unique UUID of the station (`self.station.uuid`) as the identifier, ensuring each station is registered as a distinct device. It also populates relevant metadata like `name`, `manufacturer`, and `configuration_url` from the station data. Crucially, it sets `entry_type=DeviceEntryType.SERVICE`, which is the correct approach for integrations that represent a service or a logical grouping rather than a physical hardware device.

The `PegelOnlineSensor` class in `homeassistant/components/pegel_online/sensor.py` inherits from `PegelOnlineEntity`, thereby automatically inheriting the configured `_attr_device_info` and linking each sensor entity (like water level, temperature, etc.) to the corresponding station's device entry.

This implementation aligns perfectly with the rule's requirements and best practices for representing services or locations as devices in Home Assistant.

## Suggestions

No suggestions needed.

```

_Created at 2025-05-25 11:24:03. Prompt tokens: 5878, Output tokens: 542, Total tokens: 7230_
