```markdown
# pegel_online: entity-device-class

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [entity-device-class](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-device-class) |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires entities to use device classes where possible to provide context to Home Assistant, which benefits features like unit conversion, voice control, UI representation, and more. The rule states there are no exceptions.

The `pegel_online` integration provides various sensor entities representing measurements from water measuring stations. Looking at the `homeassistant/components/pegel_online/sensor.py` file, the integration defines a list of sensor entities using the `SENSORS` tuple of `PegelOnlineSensorEntityDescription` objects.

The integration successfully uses device classes for many of the sensor types:
*   `air_temperature` uses `SensorDeviceClass.TEMPERATURE`.
*   `clearance_height` uses `SensorDeviceClass.DISTANCE`.
*   `ph_value` uses `SensorDeviceClass.PH`.
*   `water_speed` uses `SensorDeviceClass.SPEED`.
*   `water_flow` uses `SensorDeviceClass.VOLUME_FLOW_RATE`.
*   `water_temperature` uses `SensorDeviceClass.TEMPERATURE`.

However, the following sensor types do *not* have a device class assigned in their description:
*   `oxygen_level`
*   `water_level`

While `oxygen_level` might not have a perfectly fitting device class (its unit 'mg/l' doesn't directly align with standard `concentration` units like ppm or %), `water_level` reports a height or level, typically in units like 'cm'. Home Assistant's `SensorDeviceClass.DISTANCE` supports distance units like 'cm', 'm', etc. Therefore, `water_level` could reasonably use `SensorDeviceClass.DISTANCE` as its device class, as it represents a distance/height measurement relative to a reference point.

Since `water_level` could use an existing device class (`DISTANCE`) but does not, the integration does not fully follow the rule "where possible".

## Suggestions

To make the integration compliant with the `entity-device-class` rule, the following change should be made:

1.  **Assign `SensorDeviceClass.DISTANCE` to the `water_level` sensor:**
    *   In `homeassistant/components/pegel_online/sensor.py`, locate the `PegelOnlineSensorEntityDescription` for `"water_level"`.
    *   Add `device_class=SensorDeviceClass.DISTANCE` to its definition.

    ```diff
    --- a/homeassistant/components/pegel_online/sensor.py
    +++ b/homeassistant/components/pegel_online/sensor.py
    @@ -68,6 +68,7 @@
         key="water_level",
         translation_key="water_level",
         state_class=SensorStateClass.MEASUREMENT,
+        device_class=SensorDeviceClass.DISTANCE,
         measurement_fn=lambda data: data.water_level,
     ),
     PegelOnlineSensorEntityDescription(

    ```
This change correctly categorizes the `water_level` entity, allowing Home Assistant to handle its unit and representation appropriately, fulfilling the requirement of using a device class where possible.

Regarding `oxygen_level`, if no suitable device class exists (e.g., `concentration` doesn't fit the unit `mg/l`), it's acceptable not to assign one. However, adding the `DISTANCE` class to `water_level` is a clear improvement based on available device classes and the nature of the measurement.
```

_Created at 2025-05-25 11:24:50. Prompt tokens: 5878, Output tokens: 877, Total tokens: 8131_
