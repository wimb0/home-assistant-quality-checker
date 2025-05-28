# overkiz: devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/devices)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `devices` rule requires integrations to create devices in the Home Assistant device registry and populate their information as completely as possible, including fields like name, serial number, hardware/software versions, manufacturer, model, model ID, and connections.

This rule applies to the `overkiz` integration as it manages a central hub (gateway) and numerous connected end-devices (covers, sensors, lights, etc.), all of which should be represented as devices in Home Assistant.

The `overkiz` integration currently creates devices for both the gateway and the individual end-devices.

**Gateway Device (in `__init__.py`):**
The gateway device is created using `device_registry.async_get_or_create`.
It populates:
*   `identifiers`
*   `model` (from `gateway.sub_type`)
*   `manufacturer` (from `client.server.manufacturer`)
*   `name` (from `gateway.type` or `gateway.id`)
*   `sw_version` (from `gateway.connectivity.protocol_version`)
*   `configuration_url`

However, for the gateway device, it does not populate:
*   `connections` (e.g., MAC address, despite being available during DHCP discovery)
*   `serial_number`
*   `hw_version`
*   `model_id`

**End-Device Entities (in `entity.py` via `OverkizEntity.generate_device_info`):**
Entities associated with Overkiz end-devices populate `DeviceInfo` with:
*   `identifiers` (based on `base_device_url`)
*   `name` (from `self.device.label`)
*   `manufacturer` (derived from attributes/states or hub manufacturer)
*   `model` (derived from states or widget value)
*   `sw_version` (from `OverkizAttribute.CORE_FIRMWARE_REVISION`)
*   `hw_version` (mapped to `self.device.controllable_name`)
*   `suggested_area`
*   `via_device` (linking to the gateway device)
*   `configuration_url`

For these end-device entities, `DeviceInfo` is quite comprehensive. However, it does not attempt to populate:
*   `serial_number` (e.g., from `OverkizState.CORE_SERIAL_NUMBER`)
*   `model_id` (a more specific product identifier beyond the current `model`)
*   `connections` (e.g., mapping device protocol and address to an HA connection type)

While the integration does a good job, the missing fields, especially `serial_number` for entities and `connections` for the gateway (which are explicitly mentioned in the rule's example implementation or are common practice for hub devices), mean the integration does not fully follow the rule. Therefore, the status is "todo".

## Suggestions

To make the `overkiz` integration fully compliant with the `devices` rule, consider the following improvements:

1.  **For End-Device Entities (`homeassistant/components/overkiz/entity.py`):**
    *   **Populate `serial_number`:**
        Modify the `generate_device_info` method in `OverkizEntity` to attempt to fetch and include the serial number. `pyoverkiz.enums.OverkizState.CORE_SERIAL_NUMBER` (`core:SerialNumberState`) is a potential source.
        ```python
        # In OverkizEntity.generate_device_info()
        
        # ... (existing code for manufacturer, model) ...

        serial_number = self.executor.select_state(OverkizState.CORE_SERIAL_NUMBER)
        
        # ...

        return DeviceInfo(
            # ... existing fields ...
            serial_number=str(serial_number) if serial_number else None,
            # ... existing fields ...
        )
        ```
    *   **Populate `model_id`:**
        Investigate if a more specific product identifier (model ID) is available in device states or attributes beyond what is currently used for `model`. If found, populate the `model_id` field in `DeviceInfo`. The `model` field currently uses `OverkizState.CORE_MODEL`, `OverkizState.CORE_PRODUCT_MODEL_NAME`, or `OverkizState.IO_MODEL`. If `CORE_PRODUCT_MODEL_NAME` is a better fit for `model_id`, then `model` could use the other fallbacks, and `model_id` could use `CORE_PRODUCT_MODEL_NAME`.
    *   **(Optional/Advanced) Populate `connections`:**
        This is more complex. If `self.device.protocol` (e.g., `Protocol.ZIGBEE`, `Protocol.IO_HOME_CONTROL`) and a unique device address within that protocol could be mapped to Home Assistant `CONNECTION_*` constants (e.g., `dr.CONNECTION_ZIGBEE`), this would enhance device information. This might require new constants or careful mapping.

2.  **For the Gateway Device (`homeassistant/components/overkiz/__init__.py`):**
    *   **Populate `connections`:**
        The gateway's MAC address is available during DHCP discovery (`DhcpServiceInfo.macaddress` in `config_flow.py`). This MAC address should be stored in the `ConfigEntry.data`. Then, in `async_setup_entry`, retrieve it and add it to the gateway's `DeviceInfo`.
        Example modification in `config_flow.py` (conceptual, needs to be added to `user_input` passed to `async_create_entry`):
        ```python
        # In OverkizConfigFlow.async_step_dhcp
        # self._discovered_mac = discovery_info.macaddress 
        # ... ensure this gets into the data for async_create_entry

        # In async_setup_entry in __init__.py
        gateway_mac = entry.data.get(CONF_MAC_ADDRESS) # Assuming CONF_MAC_ADDRESS is used to store it
        # ...
        device_registry.async_get_or_create(
            # ... existing fields ...
            connections={(dr.CONNECTION_NETWORK_MAC, gateway_mac)} if gateway_mac else None,
            # ...
        )
        ```
        If storing the MAC address is too complex, and if the `gateway.id` (which is used for `identifiers`) is derived from or is the MAC address (though typically it's a different format), it could be adapted. However, using the actual MAC from discovery is preferred.
    *   **Populate `serial_number`:**
        The `gateway.id` from `pyoverkiz` (e.g., `XXXX-XXXX-XXXX`) is often a unique identifier for the hardware and could serve as the `serial_number`.
        ```python
        # In async_setup_entry in __init__.py
        device_registry.async_get_or_create(
            # ... existing fields ...
            serial_number=gateway.id, # If gateway.id is suitable as a serial number
            # ...
        )
        ```
        Alternatively, if the `pyoverkiz.models.Gateway` object provides a more direct serial number attribute in the future, use that.
    *   **Populate `hw_version`:**
        Consider using `gateway.type.value` or another relevant field from the `gateway` object if it represents a hardware version or a distinct hardware model specifier. The `gateway.sub_type` is currently used for `model`.
        ```python
        # In async_setup_entry in __init__.py
        device_registry.async_get_or_create(
            # ... existing fields ...
            hw_version=str(gateway.type.value) if gateway.type else None, # Example
            # ...
        )
        ```

By implementing these suggestions, the `overkiz` integration will provide more complete device information, enhancing the user experience and aligning more closely with the `devices` quality scale rule.

_Created at 2025-05-28 12:25:40. Prompt tokens: 86982, Output tokens: 1917, Total tokens: 93756_
