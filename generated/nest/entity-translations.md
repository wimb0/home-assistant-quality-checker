# nest: entity-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [entity-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-translations)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `entity-translations` rule applies to the `nest` integration because it creates entities (camera, climate, event, sensor) that should have user-friendly, translatable names to enhance accessibility for non-English speakers.

The `nest` integration partially follows this rule:

**Compliant Entities:**

*   **Event Entities (`event.py`):**
    *   `NestTraitEventEntity` sets `_attr_has_entity_name = True`.
    *   It utilizes `entity_description.translation_key` (e.g., `"chime"`, `"motion"`) defined in `NestEventEntityDescription`.
    *   Corresponding translations are present in `homeassistant/components/nest/strings.json`:
        ```json
        "entity": {
          "event": {
            "chime": {
              "name": "Chime"
            },
            "motion": {
              "name": "[%key:component::event::entity_component::motion::name%]"
            }
          }
        }
        ```
    *   This correctly provides translated names like "Device Name Chime" or "Device Name Motion".

*   **Sensor Entities (`sensor.py`):**
    *   `SensorBase` (and thus `TemperatureSensor` and `HumiditySensor`) sets `_attr_has_entity_name = True`.
    *   `TemperatureSensor` sets `_attr_device_class = SensorDeviceClass.TEMPERATURE`.
    *   `HumiditySensor` sets `_attr_device_class = SensorDeviceClass.HUMIDITY`.
    *   These sensor entities correctly fall under the rule's exception: their platform is `sensor`, they have a `device_class` set, and they are intended to use the device class name. Home Assistant core provides translations for these device classes (e.g., "Temperature", "Humidity"). Thus, they will be named like "Device Name Temperature", which is compliant.

**Non-Compliant Entities:**

*   **Camera Entities (`camera.py`):**
    *   `NestCameraBaseEntity` (superclass for `NestRTSPEntity` and `NestWebRTCEntity`) sets `_attr_has_entity_name = True` and `_attr_name = None` (see `homeassistant/components/nest/camera.py`, lines 92-93).
    *   It does not set `_attr_translation_key`.
    *   The `camera` platform is not covered by the device class naming exception.
    *   As a result, the entity-specific part of the name is effectively empty, and the camera entity's name defaults to just the device name (e.g., "My Nest Hub Max"). The rule intends for a translatable name part like "Camera" to be appended (e.g., "My Nest Hub Max Camera").

*   **Climate Entities (`climate.py`):**
    *   `ThermostatEntity` sets `_attr_has_entity_name = True` and `_attr_name = None` (see `homeassistant/components/nest/climate.py`, lines 65-67).
    *   It does not set `_attr_translation_key`.
    *   The `climate` platform is not covered by the device class naming exception.
    *   Similar to cameras, the entity name defaults to just the device name (e.g., "Living Room Thermostat"). A translatable name part like "Thermostat" should be appended (e.g., "Living Room Thermostat Thermostat").

Because camera and climate entities do not provide a translatable entity name component, the integration does not fully follow the `entity-translations` rule.

## Suggestions

To make the `nest` integration fully compliant with the `entity-translations` rule, the following changes are recommended for camera and climate entities:

1.  **For Camera Entities:**
    *   In `homeassistant/components/nest/camera.py`, modify `NestCameraBaseEntity` to include a `_attr_translation_key`:
        ```python
        class NestCameraBaseEntity(Camera, ABC):
            _attr_has_entity_name = True
            _attr_name = None
            _attr_translation_key = "camera"  # Add this line
            _attr_is_streaming = True
            _attr_supported_features = CameraEntityFeature.STREAM
            # ...
        ```
    *   In `homeassistant/components/nest/strings.json`, add the corresponding translation under the `entity.camera` key:
        ```json
        {
          "application_credentials": {
            // ...
          },
          "config": {
            // ...
          },
          "device_automation": {
            // ...
          },
          "entity": {
            "camera": {  // Add this section
              "camera": {
                "name": "Camera"
              }
            },
            "event": {
              "chime": {
                "name": "Chime",
                // ...
              },
              "motion": {
                "name": "[%key:component::event::entity_component::motion::name%]",
                // ...
              }
            }
            // ... potentially other platforms like climate here
          },
          "selector": {
            // ...
          }
        }
        ```

2.  **For Climate Entities:**
    *   In `homeassistant/components/nest/climate.py`, modify `ThermostatEntity` to include a `_attr_translation_key`:
        ```python
        class ThermostatEntity(ClimateEntity):
            _attr_min_temp = MIN_TEMP
            _attr_max_temp = MAX_TEMP
            _attr_has_entity_name = True
            _attr_should_poll = False
            _attr_name = None
            _attr_translation_key = "thermostat"  # Add this line
            # ...
        ```
    *   In `homeassistant/components/nest/strings.json`, add the corresponding translation under the `entity.climate` key. If the `entity.camera` section was added as above, it would look like this:
        ```json
        {
          // ... other keys ...
          "entity": {
            "camera": {
              "camera": {
                "name": "Camera"
              }
            },
            "climate": { // Add this section
              "thermostat": {
                "name": "Thermostat"
              }
            },
            "event": {
              "chime": {
                "name": "Chime",
                // ...
              },
              "motion": {
                "name": "[%key:component::event::entity_component::motion::name%]",
                // ...
              }
            }
          },
          // ... other keys ...
        }
        ```

**Why these changes satisfy the rule:**

*   Setting `_attr_has_entity_name = True` and `_attr_translation_key = "your_key"` instructs Home Assistant to use a translated string for the entity-specific part of its name.
*   Adding the corresponding `name` field in `strings.json` under `entity.<platform>.<your_key>` provides the actual translation (defaulting to English).
*   This will result in entity names like "Device Name Camera" or "Device Name Thermostat", where "Camera" and "Thermostat" are translatable strings, making the integration more accessible globally.

_Created at 2025-05-28 23:10:54. Prompt tokens: 32404, Output tokens: 1783, Total tokens: 38123_
