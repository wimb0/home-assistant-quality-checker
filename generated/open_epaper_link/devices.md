# open_epaper_link: devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/devices)                                                     |
| Status | **todo**                                       |
| Reason | The `DeviceInfo` for both the tags and the Access Point (AP) is not populated as completely as recommended by the rule's example, missing several fields that would enhance user experience. |

## Overview

The `devices` rule requires that integrations creating representations of physical devices or services should make the device information in the device registry as complete as possible. This is crucial for a good user experience, allowing users to easily identify and manage their devices.

This rule applies to the `open_epaper_link` integration as it manages physical E-Paper Tags (ESLs) and an Access Point (AP), both of which are represented as devices in Home Assistant. The integration creates entities (sensors, cameras, buttons, etc.) associated with these devices.

The integration currently attempts to follow this rule by providing `DeviceInfo` for both the AP and the individual tags. However, the information provided is not as complete as it could be, especially when compared to the example provided in the rule description.

**For E-Paper Tags (ESL Devices):**
The primary `DeviceInfo` for tags is populated in `sensor.py` within the `OpenEPaperLinkTagSensor` class.
```python
# homeassistant/components/open_epaper_link/sensor.py
# class OpenEPaperLinkTagSensor:
#   __init__():
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._tag_mac)},
            name=name_base,
            manufacturer="OpenEPaperLink",
            model=hw_string,
            via_device=(DOMAIN, "ap"),
            sw_version=f"0x{int(firmware_version, 16):X}" if firmware_version else "Unknown",
            serial_number=self._tag_mac,
            hw_version=f"{width}x{height}",
        )
```
This definition includes:
*   `identifiers`
*   `name`
*   `manufacturer`
*   `model`
*   `via_device`
*   `sw_version`
*   `serial_number`
*   `hw_version`

However, it is missing:
*   `connections`: For network-connected devices, this typically includes MAC addresses. Tags have MAC addresses which are used as identifiers.
*   `model_id`: A more specific, non-human-readable model identifier (e.g., the numeric `hw_type`).

**For the Access Point (AP) Device:**
The primary `DeviceInfo` for the AP is populated in `sensor.py` within the `OpenEPaperLinkAPSensor` class.
```python
# homeassistant/components/open_epaper_link/sensor.py
# class OpenEPaperLinkAPSensor:
#   __init__():
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "ap")},
            name="OpenEPaperLink AP",
            model=self._hub.ap_model, # Derived from ap_env
            manufacturer="OpenEPaperLink",
        )
```
This definition includes:
*   `identifiers`
*   `name`
*   `model`
*   `manufacturer`

However, it is missing several fields that are generally expected for a hub/gateway device:
*   `connections`: The AP connects via IP and has a MAC address.
*   `serial_number`: Typically the MAC address for network devices.
*   `sw_version`: The firmware version of the AP.
*   `hw_version`: The hardware version/revision of the AP.
*   `model_id`: A more specific model identifier, potentially the `ap_env` string.

While other entities (buttons, switches, etc.) correctly link to these devices using their `device_info` property, the completeness of the device registry entry itself, established by the sensor entities, is what's being assessed.

Because several recommended fields from the rule's example `DeviceInfo` are missing for both tags and especially for the AP, the integration does not fully follow the rule to make device information "as complete as possible."

## Suggestions

To make the `open_epaper_link` integration compliant with the `devices` rule by providing more complete `DeviceInfo`:

**1. For E-Paper Tag Devices (`OpenEPaperLinkTagSensor` in `sensor.py`):**

*   **Add `connections`:** Include the tag's MAC address in the `connections` set.
*   **Add `model_id`:** Use the numeric hardware type (`hw_type`) as the `model_id`.

   Modify the `__init__` method of `OpenEPaperLinkTagSensor` as follows:

   ```python
   # homeassistant/components/open_epaper_link/sensor.py
   from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC # Add this import
   # ... other imports ...

   class OpenEPaperLinkTagSensor(OpenEPaperLinkBaseSensor):
       def __init__(self, hub, tag_mac: str, description: OpenEPaperLinkSensorEntityDescription) -> None:
           super().__init__(hub, description)
           self._tag_mac = tag_mac

           name_base = self._hub.get_tag_data(tag_mac).get("tag_name", tag_mac)
           self._attr_has_entity_name = True
           self._attr_translation_key = description.key
           self._attr_unique_id = f"{tag_mac}_{description.key}"
           self.entity_id = f"{DOMAIN}.{tag_mac.lower()}_{description.key}"

           tag_data = self._hub.get_tag_data(self._tag_mac)
           firmware_version = str(tag_data.get("version", ""))
           hw_type = tag_data.get("hw_type", 0) # hw_type is an int
           hw_string = get_hw_string(hw_type)
           width, height = get_hw_dimensions(hw_type)

           self._attr_device_info = DeviceInfo(
               connections={(CONNECTION_NETWORK_MAC, self._tag_mac)}, # ADDED
               identifiers={(DOMAIN, self._tag_mac)},
               name=name_base,
               manufacturer="OpenEPaperLink",
               model=hw_string,
               model_id=str(hw_type), # ADDED - Cast hw_type to string
               via_device=(DOMAIN, "ap"),
               sw_version=f"0x{int(firmware_version, 16):X}" if firmware_version else "Unknown",
               serial_number=self._tag_mac,
               hw_version=f"{width}x{height}",
           )
   ```

**2. For the Access Point (AP) Device (`OpenEPaperLinkAPSensor` in `sensor.py`):**

*   **Enhance `hub.py`:**
    *   Modify `Hub.async_update_ap_info` in `hub.py` to fetch and store AP's MAC address and software version from the `/sysinfo` endpoint. The `/sysinfo` endpoint typically provides fields like `"mac"` and `"version"`. Hardware version might be derived from `"board"` or `"platform"` if available, or might not be explicitly provided by the AP.
    ```python
    # homeassistant/components/open_epaper_link/hub.py
    # class Hub:
    #   In __init__:
    #     self.ap_sw_version: str | None = None
    #     self.ap_mac: str | None = None
    #     self.ap_hw_version: str | None = None # Optional, if available

    #   In async_update_ap_info:
        async def async_update_ap_info(self) -> None:
            """Force update of AP configuration."""
            try:
                async with async_timeout.timeout(10):
                    async with self._session.get(f"http://{self.host}/sysinfo") as response:
                        if response.status != 200:
                            _LOGGER.error("Failed to fetch AP sys info: HTTP %s", response.status)
                            return

                        data = await response.json()
                        self.ap_env = data.get("env")
                        self.ap_model = self._format_ap_model(self.ap_env)
                        self.ap_sw_version = data.get("version") # ADDED
                        self.ap_mac = data.get("mac") # ADDED
                        # Optionally, try to get a hardware version
                        # self.ap_hw_version = data.get("board") or data.get("platform") # EXAMPLE
            except Exception as err:
                _LOGGER.error(f"Error updating AP info: {err}")
    ```

*   **Update `DeviceInfo` in `OpenEPaperLinkAPSensor`:**
    *   Use the newly available hub properties (`ap_mac`, `ap_sw_version`, etc.) to populate `connections`, `serial_number`, `sw_version`, `hw_version`, and `model_id`.

   Modify the `__init__` method of `OpenEPaperLinkAPSensor` as follows:

   ```python
   # homeassistant/components/open_epaper_link/sensor.py
   from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC # Add if not already there
   from homeassistant.const import CONF_IP_ADDRESS # Add this import

   # ... other imports ...

   class OpenEPaperLinkAPSensor(OpenEPaperLinkBaseSensor):
       def __init__(self, hub: Hub, description: OpenEPaperLinkSensorEntityDescription) -> None:
           super().__init__(hub, description)
           self._attr_has_entity_name = True
           self._attr_translation_key = description.key
           self._attr_unique_id = f"{self._hub.entry.entry_id}_{description.key}"

           connections_val = set()
           if self._hub.ap_mac:
               connections_val.add((CONNECTION_NETWORK_MAC, self._hub.ap_mac))
           elif self._hub.host: # Fallback to IP if MAC not available from hub
               connections_val.add((CONF_IP_ADDRESS, self._hub.host))

           device_info_attrs = {
               "identifiers": {(DOMAIN, "ap")},
               "name": "OpenEPaperLink AP",
               "manufacturer": "OpenEPaperLink",
               "model": self._hub.ap_model, # Already present (uses ap_env)
           }
           if connections_val:
               device_info_attrs["connections"] = connections_val
           if self._hub.ap_mac:
               device_info_attrs["serial_number"] = self._hub.ap_mac
           if self._hub.ap_sw_version:
               device_info_attrs["sw_version"] = self._hub.ap_sw_version
           if hasattr(self._hub, 'ap_hw_version') and self._hub.ap_hw_version: # If you add ap_hw_version to Hub
               device_info_attrs["hw_version"] = self._hub.ap_hw_version
           if self._hub.ap_env: # ap_env is a good candidate for model_id
               device_info_attrs["model_id"] = self._hub.ap_env

           self._attr_device_info = DeviceInfo(**device_info_attrs)
   ```

By implementing these changes, the device information for both tags and the AP will be more complete, aligning better with the `devices` rule and improving the user experience within Home Assistant. Remember to add necessary imports like `CONNECTION_NETWORK_MAC` and `CONF_IP_ADDRESS`.

_Created at 2025-05-14 20:55:12. Prompt tokens: 60471, Output tokens: 2784, Total tokens: 69714_
