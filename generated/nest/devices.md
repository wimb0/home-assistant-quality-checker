# nest: devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/devices)                                                     |
| Status | **todo**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `devices` rule requires integrations that represent physical devices or services to create device entries in Home Assistant's device registry and populate them with as much information as possible. This helps users identify and manage their devices.

The `nest` integration interfaces with physical Nest devices (thermostats, cameras, doorbells) and correctly creates device entries for them. It uses a helper class `NestDeviceInfo` (in `homeassistant/components/nest/device_info.py`) to generate the `DeviceInfo` object associated with its entities.

Currently, `NestDeviceInfo` populates the following fields:
*   `identifiers`: Using the unique API device name (e.g., `enterprises/project-id/devices/device-id`).
*   `manufacturer`: Statically set to "Google Nest".
*   `model`: A generic device type derived from the API's device type (e.g., "Camera", "Thermostat" via `DEVICE_TYPE_MAP`).
*   `name`: The custom name from Nest or a name derived from its structure/room.
*   `suggested_area`: Derived from Nest's structure/room information.

While this provides basic device information, several standard `DeviceInfo` fields that could enhance device representation are not populated:

1.  **`sw_version` (Software Version):** The Nest SDM API's `InfoTrait` typically provides a `softwareVersion` field. This is not currently used by `NestDeviceInfo`.
2.  **`serial_number` (Serial Number):** While the full device resource name is used as an identifier, the specific device ID part (which often serves as a serial number) is not explicitly extracted and set in the `serial_number` field.
3.  **`via_device` (Via Device):** Nest devices are cloud-connected. Linking them to the config entry representing the cloud account (via `via_device=(DOMAIN, config_entry.entry_id)`) is a good practice to show the relationship.
4.  **`model` (Specific Model):** The current `model` field uses a generic type (e.g., "Thermostat"). If the SDM API provides a more specific hardware model string (e.g., "Nest Learning Thermostat, 3rd Gen"), using that would be preferable. However, the SDM API might not expose this level of detail easily beyond the `type` field.

Due to the missing `sw_version`, `serial_number`, and `via_device` (and potentially a more specific `model` if available), the integration does not fully meet the rule's requirement for providing device information "as complete as possible."

## Suggestions

To make the `nest` integration compliant with the `devices` rule by providing more complete device information, consider the following changes primarily within `homeassistant/components/nest/device_info.py` and the entity setup:

1.  **Add Software Version (`sw_version`):**
    *   Modify `NestDeviceInfo.device_info` to extract and include the software version.
    *   The `google_nest_sdm.device.Device` object (passed as `self._device`) contains traits. The `InfoTrait` (typically `sdm.devices.traits.Info`) should have a `software_version` attribute (the SDM API calls this `softwareVersion`).
    *   Code example for `device_info.py`:
        ```python
        # In class NestDeviceInfo:
        # ...
        @property
        def device_info(self) -> DeviceInfo:
            # ... (other fields) ...
            sw_version_val = None
            if InfoTrait.NAME in self._device.traits:
                info_trait: InfoTrait = self._device.traits[InfoTrait.NAME]
                # Assuming the library exposes software_version attribute,
                # which corresponds to softwareVersion from SDM API
                if hasattr(info_trait, 'software_version'):
                    sw_version_val = info_trait.software_version
                elif hasattr(info_trait, 'softwareVersion'): # Or whatever the attr is called
                    sw_version_val = info_trait.softwareVersion


            return DeviceInfo(
                identifiers={(DOMAIN, self._device.name)},
                manufacturer=self.device_brand,
                model=self.device_model,
                name=self.device_name,
                suggested_area=self.suggested_area,
                sw_version=sw_version_val, # Add this line
                # ... other new fields below
            )
        ```

2.  **Add Serial Number (`serial_number`):**
    *   The `self._device.name` is the full resource path (e.g., `enterprises/project-id/devices/actual-device-id`). Extract the `actual-device-id` part.
    *   Code example for `device_info.py`:
        ```python
        # In class NestDeviceInfo:
        # ...
        @property
        def device_info(self) -> DeviceInfo:
            # ...
            serial_num = None
            if self._device.name:
                try:
                    # Assuming name is like 'enterprises/project-id/devices/device-id'
                    serial_num = self._device.name.rsplit('/', 1)[-1]
                except IndexError:
                    pass # Could not parse

            return DeviceInfo(
                # ...
                serial_number=serial_num, # Add this line
                # ...
            )
        ```

3.  **Add Via Device (`via_device`):**
    *   This requires passing the `config_entry.entry_id` to `NestDeviceInfo`.
    *   Modify `NestDeviceInfo.__init__` to accept `entry_id: str | None`.
        ```python
        # In homeassistant/components/nest/device_info.py
        class NestDeviceInfo:
            def __init__(self, device: Device, entry_id: str | None = None) -> None:
                self._device = device
                self._entry_id = entry_id # Store entry_id
        # ...
            @property
            def device_info(self) -> DeviceInfo:
                # ...
                via_device_tuple = None
                if self._entry_id:
                    via_device_tuple = (DOMAIN, self._entry_id)

                return DeviceInfo(
                    # ...
                    via_device=via_device_tuple, # Add this line
                    # ...
                )
        ```
    *   Update all entity platform setup files (e.g., `camera.py`, `climate.py`, `sensor.py`, `event.py`) to pass `entry.entry_id` when instantiating `NestDeviceInfo` or when creating entity instances that use it.
        For example, in `homeassistant/components/nest/sensor.py`:
        ```python
        # In class SensorBase:
        # def __init__(self, device: Device) -> None: # Old
        def __init__(self, device: Device, entry_id: str) -> None: # New
            """Initialize the sensor."""
            self._device = device
            # self._device_info = NestDeviceInfo(device) # Old
            self._device_info_helper = NestDeviceInfo(device, entry_id) # New, assuming you rename
            self._attr_unique_id = f"{device.name}-{self.device_class}"
            self._attr_device_info = self._device_info_helper.device_info

        # In async_setup_entry for sensor.py:
        # ...
        for device in entry.runtime_data.device_manager.devices.values():
            if TemperatureTrait.NAME in device.traits:
                # entities.append(TemperatureSensor(device)) # Old
                entities.append(TemperatureSensor(device, entry.entry_id)) # New
            if HumidityTrait.NAME in device.traits:
                # entities.append(HumiditySensor(device)) # Old
                entities.append(HumiditySensor(device, entry.entry_id)) # New
        ```
        This pattern needs to be applied consistently across all entity types that use `NestDeviceInfo`.

By implementing these changes, the `nest` integration will provide a more complete and standardized set of device information, aligning better with the `devices` quality scale rule and improving the user experience.

_Created at 2025-05-28 23:02:03. Prompt tokens: 32342, Output tokens: 1989, Total tokens: 39360_
