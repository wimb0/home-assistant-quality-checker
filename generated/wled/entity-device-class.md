# wled: entity-device-class

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [entity-device-class](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-device-class)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-device-class` rule requires integrations to assign device classes to their entities wherever a suitable device class exists. This provides context to Home Assistant for UI representation, voice control, and other functionalities.

The `wled` integration creates several entity types, including update, sensor, button, light, switch, number, and select entities. The rule applies to platforms like sensor, update, button, and switch, which have defined device classes in Home Assistant.

**Positive Aspects:**
*   **Update Entity:** The `WLEDUpdateEntity` in `update.py` correctly sets `_attr_device_class = UpdateDeviceClass.FIRMWARE`.
*   **Button Entity:** The `WLEDRestartButton` in `button.py` correctly sets `_attr_device_class = ButtonDeviceClass.RESTART`.
*   **Sensor Entities (Partial):** Most sensor entities in `sensor.py` utilize appropriate `SensorDeviceClass` values where a clear match exists (e.g., `CURRENT`, `TIMESTAMP`, `DATA_SIZE`, `SIGNAL_STRENGTH` for RSSI). For some sensors like "LED count" or "Wi-Fi Channel", there isn't a specific `SensorDeviceClass` that directly applies, so their omission is understandable.
*   **Light, Number, Select Entities:** These entity platforms (`light.py`, `number.py`, `select.py`) generally do not have a broad set of standard device classes comparable to sensors or binary sensors. For example, `LightEntity` does not have a `device_class` property. The WLED entities for speed and intensity (`number.py`) do not map to any existing `NumberDeviceClass`. Similarly, `SelectEntity` does not have defined device classes. Therefore, the absence of device classes for these specific WLED entities is acceptable.

**Areas for Improvement:**
The integration does not fully follow the rule in the following areas:

1.  **IP Address Sensor:** In `sensor.py`, the sensor representing the device's IP address (key: `"ip"`) does not have a `device_class` assigned. The `SensorDeviceClass.IP_ADDRESS` is available and suitable for this type of sensor.
    ```python
    # sensor.py
    SENSORS: tuple[WLEDSensorEntityDescription, ...] = (
        # ...
        WLEDSensorEntityDescription(
            key="ip",
            translation_key="ip",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda device: device.info.ip,
        ),
        # ...
    )
    ```

2.  **Switch Entities:** In `switch.py`, none of the switch entities (`WLEDNightlightSwitch`, `WLEDSyncSendSwitch`, `WLEDSyncReceiveSwitch`, `WLEDReverseSwitch`) have a `device_class` assigned. While these are not outlets, `SwitchDeviceClass.SWITCH` is the appropriate generic device class for them.
    *   `WLEDNightlightSwitch`:
        ```python
        # switch.py
        class WLEDNightlightSwitch(WLEDEntity, SwitchEntity):
            _attr_entity_category = EntityCategory.CONFIG
            _attr_translation_key = "nightlight"
            # Missing: _attr_device_class = SwitchDeviceClass.SWITCH
        ```
    *   `WLEDSyncSendSwitch`, `WLEDSyncReceiveSwitch`, `WLEDReverseSwitch` also lack this attribute.

Because these specific device classes are available and applicable, their omission means the integration is not fully compliant with the "Entities use device classes where possible" rule.

## Suggestions

To make the `wled` integration compliant with the `entity-device-class` rule, the following changes are recommended:

1.  **Update IP Address Sensor:**
    Modify the `WLEDSensorEntityDescription` for the IP address sensor in `sensor.py` to include `device_class=SensorDeviceClass.IP_ADDRESS`.

    *File: `sensor.py`*
    ```python
    # ...
    from homeassistant.components.sensor import (
        SensorDeviceClass, # Ensure SensorDeviceClass is imported
        SensorEntity,
        SensorEntityDescription,
        SensorStateClass,
    )
    # ...

    SENSORS: tuple[WLEDSensorEntityDescription, ...] = (
        # ...
        WLEDSensorEntityDescription(
            key="ip",
            translation_key="ip",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=SensorDeviceClass.IP_ADDRESS,  # Add this line
            value_fn=lambda device: device.info.ip,
        ),
    )
    ```
    **Reasoning:** `SensorDeviceClass.IP_ADDRESS` provides specific context that this sensor represents an IP address, which can be used by Home Assistant for display or other purposes.

2.  **Update Switch Entities:**
    Add `_attr_device_class = SwitchDeviceClass.SWITCH` to all switch entity classes in `switch.py`.

    *File: `switch.py`*
    ```python
    # ...
    from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity # Ensure SwitchDeviceClass is imported
    # ...

    class WLEDNightlightSwitch(WLEDEntity, SwitchEntity):
        """Defines a WLED nightlight switch."""

        _attr_entity_category = EntityCategory.CONFIG
        _attr_translation_key = "nightlight"
        _attr_device_class = SwitchDeviceClass.SWITCH  # Add this line

        # ...

    class WLEDSyncSendSwitch(WLEDEntity, SwitchEntity):
        """Defines a WLED sync send switch."""

        _attr_entity_category = EntityCategory.CONFIG
        _attr_translation_key = "sync_send"
        _attr_device_class = SwitchDeviceClass.SWITCH  # Add this line

        # ...

    class WLEDSyncReceiveSwitch(WLEDEntity, SwitchEntity):
        """Defines a WLED sync receive switch."""

        _attr_entity_category = EntityCategory.CONFIG
        _attr_translation_key = "sync_receive"
        _attr_device_class = SwitchDeviceClass.SWITCH  # Add this line

        # ...

    class WLEDReverseSwitch(WLEDEntity, SwitchEntity):
        """Defines a WLED reverse effect switch."""

        _attr_entity_category = EntityCategory.CONFIG
        _attr_translation_key = "reverse"
        _attr_device_class = SwitchDeviceClass.SWITCH  # Add this line
        _segment: int
        # ...
    ```
    **Reasoning:** `SwitchDeviceClass.SWITCH` is the appropriate device class for generic switches that are not outlets. Explicitly setting this provides better context to Home Assistant, aligning with the rule's intent.

By implementing these suggestions, the `wled` integration will better adhere to the `entity-device-class` quality scale rule, improving entity contextualization within Home Assistant.

_Created at 2025-05-10 23:00:58. Prompt tokens: 21265, Output tokens: 1688, Total tokens: 26059_
