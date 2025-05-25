```markdown
# fritzbox: entity-device-class

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [entity-device-class](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-device-class) |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The rule `entity-device-class` requires integrations to use device classes for entities where possible to provide context for various Home Assistant features like UI representation, voice control, and unit handling. This rule is applicable to the `fritzbox` integration as it creates various entity types.

The `fritzbox` integration generally follows this rule by applying device classes to many entities using the `device_class` attribute in `EntityDescription` or setting `_attr_device_class` directly.

*   In `homeassistant/components/fritzbox/binary_sensor.py`, most `FritzBinarySensorEntityDescription` instances define a `device_class` (`WINDOW`, `LOCK`, `BATTERY`). However, the `window_open` description is missing `device_class=BinarySensorDeviceClass.WINDOW`, which is an appropriate device class for this entity.
*   In `homeassistant/components/fritzbox/cover.py`, the `FritzboxCover` entity correctly sets `_attr_device_class = CoverDeviceClass.BLIND`.
*   In `homeassistant/components/fritzbox/light.py`, the `FritzboxLight` entity does not set a device class, which is standard practice for generic light entities unless they represent a specific type (like a fan light), so this is acceptable.
*   In `homeassistant/components/fritzbox/sensor.py`, all `FritzSensorEntityDescription` instances that represent quantifiable measurements define an appropriate `device_class` (`TEMPERATURE`, `HUMIDITY`, `BATTERY`, `POWER`, `VOLTAGE`, `CURRENT`, `ENERGY`, `TIMESTAMP`).
*   In `homeassistant/components/fritzbox/switch.py`, the `FritzboxSwitch` entity does not set a `_attr_device_class`. While not strictly mandatory for all switches, `SwitchDeviceClass.SWITCH` is generally recommended for generic on/off switches to provide better context, especially for UI and voice assistants.
*   The `button` and `climate` entities do not typically use device classes in Home Assistant, so their omission is correct.

Due to the missing applicable device classes for the `window_open` binary sensor and the `switch` entity, the integration does not fully comply with the rule.

## Suggestions

To comply with the `entity-device-class` rule, apply the appropriate device classes to the entities identified as missing them:

1.  **For the `window_open` binary sensor:**
    *   In `homeassistant/components/fritzbox/binary_sensor.py`, update the `FritzBinarySensorEntityDescription` for `window_open` to include `device_class=BinarySensorDeviceClass.WINDOW`.

    ```diff
    --- a/homeassistant/components/fritzbox/binary_sensor.py
    +++ b/homeassistant/components/fritzbox/binary_sensor.py
    @@ -62,6 +62,7 @@
     FritzBinarySensorEntityDescription(
         key="window_open",
         translation_key="window_open",
+        device_class=BinarySensorDeviceClass.WINDOW,
         suitable=lambda device: device.window_open is not None,
         is_on=lambda device: device.window_open,
     ),

    ```

2.  **For the generic `switch` entity:**
    *   In `homeassistant/components/fritzbox/switch.py`, set `_attr_device_class = SwitchDeviceClass.SWITCH` on the `FritzboxSwitch` class.

    ```diff
    --- a/homeassistant/components/fritzbox/switch.py
    +++ b/homeassistant/components/fritzbox/switch.py
    @@ -29,6 +29,8 @@
 
 class FritzboxSwitch(FritzBoxDeviceEntity, SwitchEntity):
     """The switch class for FRITZ!SmartHome switches."""
+
+    _attr_device_class = SwitchDeviceClass.SWITCH
 
     @property
     def is_on(self) -> bool:

    ```

Applying these changes will ensure that these entities benefit from the standard behaviors and representations associated with their respective device classes within Home Assistant.

```

_Created at 2025-05-25 11:36:10. Prompt tokens: 18973, Output tokens: 1047, Total tokens: 21507_
