# fritzbox: devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/devices) |
| Status | **done**                                                                 |

## Overview

The `devices` rule requires that an integration creates devices to group related entities, representing a physical device or a service, and populates the device registry with relevant information. This integration, `fritzbox`, manages multiple physical devices connected to a FRITZ!Box router (like smart plugs, thermostats, lights, etc.) as well as FRITZ!Box Smart Home templates. Therefore, the rule applies.

The `fritzbox` integration successfully implements the creation and linking of devices.

1.  **Physical Devices:** The `FritzboxDataUpdateCoordinator` in `coordinator.py` is responsible for fetching device data from the FRITZ!Box. The `_async_update_data` method explicitly uses `dr.async_get(self.hass).async_get_or_create()` to create device registry entries for main physical devices (those without a unit ID, `device.device_and_unit_id[1] is None`). It populates the device entry with good information such as `config_entry_id`, `name`, `identifiers` (using the AIN), `manufacturer`, `model`, `sw_version`, and `configuration_url`.
2.  **Entity Linking:** The base entity class for physical devices, `FritzBoxDeviceEntity` in `entity.py`, defines a `device_info` property. This property returns a `DeviceInfo` object containing `identifiers={(DOMAIN, self.data.device_and_unit_id[0])}`. This links the entity directly to the device registry entry created by the coordinator using the primary identifier (the AIN of the main device). All platform entities (binary_sensor, cover, light, sensor, switch) inherit from `FritzBoxDeviceEntity`, ensuring they are linked to their corresponding physical device entry.
3.  **Template Devices (Services):** The `FritzBoxTemplate` entity defined in `button.py` represents FRITZ!Box Smart Home templates. This entity also defines a `device_info` property. This `DeviceInfo` object is created directly by the entity and includes `name`, `identifiers` (using the template AIN), `configuration_url`, `manufacturer`, and specifies the `model` as "SmartHome Template". This effectively represents the template as a distinct device in Home Assistant, grouping related entities (though templates typically only expose a button).

Although the template device `DeviceInfo` does not explicitly set `entry_type=DeviceEntryType.SERVICE` as suggested for service representations, the integration correctly groups entities under devices and populates the device registry with sufficient information for both physical and template devices. This fulfills the core requirements of the rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-25 11:35:23. Prompt tokens: 18973, Output tokens: 666, Total tokens: 21055_
