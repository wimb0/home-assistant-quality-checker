# eheimdigital: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [eheimdigital](https://www.home-assistant.io/integrations/eheimdigital/) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `icon-translations` rule applies to the `eheimdigital` integration because it defines various entities (climate, light, number, select, sensor, switch, time) that can display icons, and it utilizes translation keys for entity naming. The rule requires that if an entity uses a `translation_key`, its icon should also be defined in an `icons.json` file using that same key, unless a device class icon is more appropriate and its context matches.

The integration partially follows this rule:
*   It includes an `icons.json` file (`homeassistant/components/eheimdigital/icons.json`).
*   Entities in the `number`, `sensor`, `switch`, and `time` platforms correctly use `translation_key` (either directly or via entity descriptions) and have corresponding icon definitions in `icons.json`.
    *   Example: `sensor.py` defines `EheimDigitalSensorDescription` with `translation_key="current_speed"`, and `icons.json` has an entry under `entity.sensor.current_speed`.
    *   Example: `switch.py` defines `EheimDigitalClassicVarioSwitch` with `_attr_translation_key = "filter_active"`, and `icons.json` has an entry under `entity.switch.filter_active`.

However, the integration does not fully follow the rule for all entity types:

1.  **Climate Entities:**
    *   The `EheimDigitalHeaterClimate` entity in `climate.py` sets `_attr_translation_key = "heater"`.
    *   There is no corresponding entry for `heater` under the `climate` domain in `homeassistant/components/eheimdigital/icons.json`. The `climate` domain is missing entirely from `icons.json`.

2.  **Light Entities:**
    *   The `EheimDigitalClassicLEDControlLight` entity in `light.py` sets `_attr_translation_key = "channel"`.
    *   There is no corresponding entry for `channel` under the `light` domain in `homeassistant/components/eheimdigital/icons.json`. The `light` domain is missing entirely from `icons.json`.

3.  **Select Entities:**
    *   `EheimDigitalSelect` entities defined in `select.py` use `translation_key="filter_mode"` via `EheimDigitalSelectDescription`.
    *   There is no corresponding entry for `filter_mode` under the `select` domain in `homeassistant/components/eheimdigital/icons.json`. The `select` domain is missing entirely from `icons.json`.

Because these entities use `_attr_translation_key` (for their names, leveraging `strings.json`), their icons should also be defined in `icons.json` to comply with the rule, unless a suitable device class icon is already serving the purpose (which is not the case for these climate, light, and select entities as they don't have specific device classes that would provide distinct icons).

## Suggestions

To make the `eheimdigital` integration compliant with the `icon-translations` rule, the following changes are recommended:

1.  **Update `homeassistant/components/eheimdigital/icons.json` to include icon definitions for the missing entities.**

    Add entries for `climate`, `light`, and `select` entities that use `_attr_translation_key`.

    **Example `icons.json` additions:**

    ```json
    {
      "entity": {
        "climate": {
          "heater": {
            "default": "mdi:thermometer-water" // Example: Or mdi:radiator, mdi:thermostat
            // Consider state-specific icons if applicable, e.g., for HVAC action
            // "state_attributes": {
            //   "hvac_action": {
            //     "heating": "mdi:fire",
            //     "idle": "mdi:radiator", // Or same as default
            //     "off": "mdi:radiator-off" // Or same as default if hvac_mode handles off
            //   }
            // }
            // Or simpler state-based on HVAC mode if 'off' state is distinct
            // "state_map": {
            //   "off": "mdi:thermostat-off" // If HVACMode.OFF has a distinct icon
            // }
          }
        },
        "light": {
          "channel": {
            "default": "mdi:led-strip-variant", // Example: Or mdi:lightbulb
            "state": {
              "on": "mdi:led-strip-variant", // Or a specific "on" icon
              "off": "mdi:led-off" // Or mdi:lightbulb if default is preferred for off
            }
          }
        },
        "number": {
          // ... existing number icons ...
        },
        "select": {
          "filter_mode": {
            "default": "mdi:filter-variant", // Example
            "state": { // Optional: if specific icons for each mode are desired
              "manual": "mdi:tune-variant",
              "pulse": "mdi:pulse",
              "bio": "mdi:leaf"
            }
          }
        },
        "sensor": {
          // ... existing sensor icons ...
        },
        "switch": {
          // ... existing switch icons ...
        },
        "time": {
          // ... existing time icons ...
        }
      }
    }
    ```

    **Explanation of changes:**
    *   **For `climate.heater`:**
        *   The `EheimDigitalHeaterClimate` entity in `climate.py` has `_attr_translation_key = "heater"`.
        *   Adding an entry `entity.climate.heater` with a `default` icon (e.g., `mdi:thermometer-water`) will provide a translated icon for this entity. You could also define icons based on `hvac_action` or `hvac_mode` if desired, though the rule primarily covers default and direct entity state icons.
    *   **For `light.channel`:**
        *   The `EheimDigitalClassicLEDControlLight` entity in `light.py` has `_attr_translation_key = "channel"`.
        *   Adding an entry `entity.light.channel` with a `default` icon (e.g., `mdi:led-strip-variant`) and potentially `state` icons for "on" and "off" will ensure its icon is managed via translations. While Home Assistant provides default icons for lights, explicitly defining them when using `_attr_translation_key` aligns with the rule's intent.
    *   **For `select.filter_mode`:**
        *   The `EheimDigitalSelect` entity for `filter_mode` in `select.py` uses `translation_key="filter_mode"`.
        *   Adding an entry `entity.select.filter_mode` with a `default` icon (e.g., `mdi:filter-variant`) makes its icon translatable. Optionally, state-specific icons for each select option (`manual`, `pulse`, `bio`) can be defined.

By implementing these additions to `icons.json`, all entities in the `eheimdigital` integration that utilize `_attr_translation_key` (or `translation_key` via entity descriptions) for their naming will also have their icons defined through the icon translation mechanism, thus fulfilling the requirements of the `icon-translations` rule.

_Created at 2025-05-27 15:41:50. Prompt tokens: 15621, Output tokens: 1802, Total tokens: 22086_
