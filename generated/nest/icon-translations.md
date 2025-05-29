# nest: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **todo**                                                                 |

## Overview

The `icon-translations` rule applies to the `nest` integration. This rule mandates the use of `icons.json` and `_attr_translation_key` for entities that require custom icons or icons that change based on state or attributes, especially when these are not adequately covered by `device_class` icons. The `nest` integration includes several entity platforms (camera, climate, event, sensor), and some of these entities could benefit from this mechanism.

Currently, the `nest` integration does **not** follow this rule.
1.  There is no `icons.json` file present in the `homeassistant/components/nest/` directory.
2.  None of the entity classes (e.g., `NestTraitEventEntity` in `event.py`, `ThermostatEntity` in `climate.py`, `NestCameraBaseEntity` in `camera.py`, `SensorBase` in `sensor.py`) set the `_attr_translation_key` attribute.
3.  Entities are not using the old `_attr_icon` method either, generally relying on `device_class` icons or default frontend behavior.

Specifically:
*   **Event Entities (`event.py`):** The `NestTraitEventEntity` that aggregates camera motion, person, and sound events (identified by `entity_description.key == EVENT_CAMERA_MOTION` and `device_class=EventDeviceClass.MOTION`) is a strong candidate. While its base icon might be for "motion," it could display more specific icons (e.g., for "person detected" or "sound detected") based on the last event type. The `EventEntity` base class stores the last `event_type` in an attribute, which can be used by icon translations.
*   **Climate Entities (`climate.py`):** `ThermostatEntity` has a `preset_mode` attribute (e.g., "eco", "none"). Icon translations could provide distinct icons for these presets, such as `mdi:leaf` for "eco" mode, as suggested by the rule's documentation ("different icons for state attribute values, for example the possible preset modes of a climate entity").
*   **Sensor Entities (`sensor.py`):** Temperature and Humidity sensors correctly use `device_class`. The rule advises against overwriting device class icons if the context is the same. While range-based icons are a possibility for these, it's not as critical as the event/climate entities, and the current device class icons (`mdi:thermometer`, `mdi:water-percent`) are standard and appropriate.
*   **Camera Entities (`camera.py`):** Cameras typically use `device_class: camera` which provides `mdi:video`. Frontend often handles state-based icon changes (e.g., for offline status). Custom icon translations might be less critical here unless specific Nest camera states warrant unique icons not covered by defaults.

## Suggestions

To make the `nest` integration compliant with the `icon-translations` rule, the following changes are recommended, focusing on the entities with the clearest benefit:

1.  **Create `icons.json`:**
    Add a new file: `homeassistant/components/nest/icons.json`.

2.  **Update `EventEntity` for Camera Events:**
    Modify `homeassistant/components/nest/event.py` for the `NestTraitEventEntity` that handles aggregated camera events (motion, person, sound).

    *   In the `__init__` method of `NestTraitEventEntity`, set `_attr_translation_key` for the specific entity description that aggregates motion, person, and sound events:
        ```python
        # In homeassistant/components/nest/event.py
        # class NestTraitEventEntity(EventEntity):
        # ...
        def __init__(
            self, entity_description: NestEventEntityDescription, device: Device
        ) -> None:
            """Initialize the event entity."""
            self.entity_description = entity_description
            self._device = device
            self._attr_unique_id = f"{device.name}-{entity_description.key}"
            self._attr_device_info = NestDeviceInfo(device).device_info
            # ---- ADD THIS ----
            if entity_description.key == EVENT_CAMERA_MOTION: # Identifies the aggregate camera event entity
                self._attr_translation_key = "nest_camera_event_type"
            # ---- END ADD ----
        ```

    *   Populate `icons.json` for this event entity. The `EventEntity` base class exposes the last triggered event type via the `event_type` attribute.
        ```json
        // In homeassistant/components/nest/icons.json
        {
          "entity": {
            "event": {
              "nest_camera_event_type": {
                "default": "mdi:motion-sensor", // Fallback icon
                "state_attributes": {
                  "event_type": { // Attribute on EventEntity to check
                    "camera_motion": "mdi:motion-sensor",
                    "camera_person": "mdi:account-alert-outline", // Or mdi:walk
                    "camera_sound": "mdi:ear-hearing" // Or mdi:volume-high
                  }
                }
              }
            }
            // Potentially add climate icons here too
          }
        }
        ```
    This change will allow the icon of the aggregate camera event entity to dynamically update based on whether the last detected event was motion, a person, or sound.

3.  **Update `ClimateEntity` for Presets (Optional but Recommended):**
    Modify `homeassistant/components/nest/climate.py` for `ThermostatEntity`.

    *   In the `__init__` method of `ThermostatEntity`, set `_attr_translation_key`:
        ```python
        # In homeassistant/components/nest/climate.py
        # class ThermostatEntity(ClimateEntity):
        # ...
        def __init__(self, device: Device) -> None:
            # ... existing initializations ...
            self._attr_translation_key = "nest_thermostat_preset"
            # ...
        ```

    *   Add corresponding entries to `homeassistant/components/nest/icons.json`:
        ```json
        // In homeassistant/components/nest/icons.json
        // (append within the "entity" object, or merge if event section already exists)
        {
          "entity": {
            // ... (event section from above)
            "climate": {
              "nest_thermostat_preset": {
                "default": "mdi:thermostat", // Default icon when preset_mode is 'none' or unknown
                "state_attributes": {
                  "preset_mode": { // Attribute on ClimateEntity to check
                    "eco": "mdi:leaf",
                    "none": "mdi:thermostat" // Can be omitted to use "default"
                  }
                }
              }
            }
          }
        }
        ```
    This will provide a distinct icon (e.g., `mdi:leaf`) when the thermostat is in "eco" preset mode.

**Why these changes satisfy the rule:**
*   They introduce `_attr_translation_key` on relevant entities.
*   They provide an `icons.json` file defining default icons and icons based on attribute states (`event_type` for events, `preset_mode` for climate).
*   This approach moves icon definitions out of Python code and into a centralized, translatable JSON file, aligning with the rule's intent to relieve the state machine and offer more flexible icon management.
*   For entities like sensors (Temperature, Humidity) where `device_class` provides a suitable and standard icon, no changes are strictly needed for icon translations, as per the rule's guidance on not unnecessarily overriding device class icons.

_Created at 2025-05-28 23:13:12. Prompt tokens: 33129, Output tokens: 1832, Total tokens: 40254_
