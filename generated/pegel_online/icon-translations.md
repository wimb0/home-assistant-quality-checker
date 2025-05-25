```markdown
# pegel_online: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **todo**                                                                 |

## Overview

This rule requires integrations to use icon translations via `_attr_translation_key` and the `icons.json` file, especially for state-based or range-based icons, and to rely on `device_class` for icons where appropriate without unnecessary overrides.

The `pegel_online` integration partially follows this rule.

Looking at the `sensor.py` file, most `PegelOnlineSensorEntityDescription` instances define a `translation_key`, such as `air_temperature`, `clearance_height`, `water_speed`, etc. The `icons.json` file exists and provides a `default` icon for each of these translation keys, which is the correct pattern for defining default icons using translations.

The `ph_value` sensor entity description does not define a `translation_key`. Instead, it relies on the `device_class: SensorDeviceClass.PH`. The rule notes that entities can get icons from the device class and should not overwrite this if the context is the same. Since the `SensorDeviceClass.PH` typically provides a standard icon for pH measurements, omitting the `translation_key` and `default` icon in `icons.json` for this specific sensor aligns with the rule's guidance.

However, the integration provides several numeric sensors like water level, air temperature, water temperature, water speed, etc. These types of sensors are often good candidates for range-based icons to visually represent different levels or states (e.g., low/medium/high water level icons, different temperature icons). The `icons.json` file for this integration only defines `default` icons and does not include any `range` or `state` based icon definitions for these numeric sensors, despite the rule highlighting this capability. While not strictly *required* to implement range-based icons, the motivation and examples in the rule suggest leveraging this feature for numeric entities where it enhances the representation and offloads icon logic from the entity code.

Therefore, while the integration uses translation keys for defaults and correctly relies on device class where applicable, it does not fully embrace the recommended use of state or range-based icon translations for its numeric sensors.

## Suggestions

To fully comply with the spirit and recommendations of the `icon-translations` rule, the `pegel_online` integration should leverage range-based icons for its numeric sensors where appropriate.

1.  **Identify suitable sensors:** Review the numeric sensors (`water_level`, `water_temperature`, `air_temperature`, `water_speed`, `water_flow`, `clearance_height`, `oxygen_level`, `ph_value`) and determine which ones would benefit from icons changing based on their numeric value range. `water_level`, `water_temperature`, and `air_temperature` are common candidates.
2.  **Add `range` definitions to `icons.json`:** For the selected sensors, add a `range` section under their respective `translation_key` entry in `icons.json`. Define numeric thresholds and corresponding icons.
    *   For example, for `water_level`:
        ```json
        {
          "entity": {
            "sensor": {
              "water_level": {
                "default": "mdi:waves-arrow-up",
                "range": {
                  "0": "mdi:waves-arrow-up",
                  "50": "mdi:waves",
                  "150": "mdi:waves-arrow-down"
                  // Define thresholds relevant to typical water levels
                }
              }
              // ... other sensors
            }
          }
        }
        ```
    *   For temperatures, a range could show different thermometer icons or colors:
        ```json
        {
          "entity": {
            "sensor": {
              "water_temperature": {
                "default": "mdi:thermometer-water",
                "range": {
                   "0": "mdi:thermometer-plus",
                   "10": "mdi:thermometer",
                   "20": "mdi:thermometer-minus"
                   // Adjust ranges and icons as appropriate
                }
              }
              // ... other sensors
            }
          }
        }
        ```
3.  **Ensure `translation_key` is set:** Confirm that `_attr_translation_key` is set correctly in `sensor.py` for all sensors that will have `range` or `state` definitions in `icons.json`. (`ph_value` does not need this if it continues to rely on device class).

By implementing range-based icons, the integration can provide a more visually dynamic and informative representation of the sensor data in the Home Assistant frontend without requiring any complex icon logic within the Python entity code.
```

_Created at 2025-05-25 11:25:27. Prompt tokens: 6665, Output tokens: 1127, Total tokens: 8907_
