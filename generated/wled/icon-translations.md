# wled: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `icon-translations` rule requires integrations to define icons in an `icons.json` file and reference them using `_attr_translation_key` in entities, rather than setting icons directly in the entity's state. This helps to relieve the state machine and allows for state-dependent icons. Entities can also inherit icons from their `device_class` if the context is appropriate and no override is needed.

The `wled` integration generally follows this rule:
*   It includes an `icons.json` file (`wled/icons.json`).
*   Most entities correctly use `_attr_translation_key` to reference icon definitions in this file (e.g., `light.py`, `select.py`, `switch.py`).
*   Some entities, like `WLEDUpdateEntity` (`update.py`) and `WLEDRestartButton` (`button.py`), appropriately rely on icons provided by their `device_class` (`UpdateDeviceClass.FIRMWARE` and `ButtonDeviceClass.RESTART`, respectively) without needing custom icon translations, which is acceptable.
*   Several sensor entities also correctly rely on their `device_class` for icons (e.g., `estimated_current` with `SensorDeviceClass.CURRENT`, `uptime` with `SensorDeviceClass.TIMESTAMP`).

However, the integration is not fully compliant because several entities set an `_attr_translation_key` for which there is no corresponding entry in `wled/icons.json`, and these entities do not have a `device_class` that would provide a suitable default icon in their context.

Specifically, the following `translation_key`s are used by entities but are missing from `wled/icons.json`:

1.  **Sensor:**
    *   `info_leds_count`: Used by `WLEDSensorEntity` for the "LED count" sensor. This sensor does not have a `device_class` assigned that would provide an icon. (see `sensor.py`)

2.  **Number:**
    *   `intensity`: Used by `WLEDNumber` for the "Intensity" number entity (when `segment == 0`). (see `number.py`)
    *   `segment_speed`: Used by `WLEDNumber` for the "Segment {segment} speed" number entity (when `segment != 0`). (see `number.py`)
    *   `segment_intensity`: Used by `WLEDNumber` for the "Segment {segment} intensity" number entity (when `segment != 0`). (see `number.py`)

For these cases, the entities will likely fall back to a generic icon for their domain or potentially no icon, which is not ideal when a specific `translation_key` has been defined.

## Suggestions

To make the `wled` integration compliant with the `icon-translations` rule, add the missing icon definitions to the `wled/icons.json` file.

1.  **For the "LED count" sensor (`info_leds_count`):**
    Add an entry under the `sensor` domain in `icons.json`. A suitable icon could be `mdi:counter` or `mdi:chip`.
    Example:
    ```json
    {
      "entity": {
        "sensor": {
          // ... existing sensor icons ...
          "info_leds_count": {
            "default": "mdi:counter"
          }
        }
        // ... other domains ...
      }
    }
    ```

2.  **For the number entities:**
    Add entries under the `number` domain in `icons.json`.
    *   `intensity`: Could use an icon like `mdi:brightness-percent` or `mdi:flare`.
    *   `segment_speed`: Could reuse `mdi:speedometer` (which is already defined for `speed`).
    *   `segment_intensity`: Could reuse `mdi:brightness-percent` or `mdi:flare`.

    Example additions to `icons.json` under `entity.number`:
    ```json
    {
      "entity": {
        "number": {
          "speed": { // Existing
            "default": "mdi:speedometer"
          },
          "intensity": { // New
            "default": "mdi:brightness-percent"
          },
          "segment_speed": { // New
            "default": "mdi:speedometer"
          },
          "segment_intensity": { // New
            "default": "mdi:brightness-percent"
          }
        }
        // ... other domains ...
      }
    }
    ```
    Note: The `strings.json` file already defines names for "Segment {segment} speed" and "Segment {segment} intensity", so corresponding icon translation keys `segment_speed` and `segment_intensity` are appropriate.

By adding these definitions, all entities that use `_attr_translation_key` will have a corresponding icon specified, fulfilling the requirements of the rule.

_Created at 2025-05-10 23:04:58. Prompt tokens: 21593, Output tokens: 1208, Total tokens: 27446_
