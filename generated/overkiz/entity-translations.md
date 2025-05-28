# overkiz: entity-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [entity-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-translations)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `entity-translations` rule requires that entities have translated names, typically by using `_attr_has_entity_name = True` along with `_attr_translation_key` and corresponding entries in `strings.json`.

The `overkiz` integration currently does not fully follow this rule for many of its entities.

1.  **Base Entity Naming (`OverkizEntity`, `OverkizDescriptiveEntity`)**:
    *   `OverkizEntity` sets `_attr_has_entity_name = True`.
    *   For sub-devices, `OverkizEntity` sets `self._attr_name = self.device.label`. The `device.label` is sourced from the Overkiz hub/device and is not translated through Home Assistant's translation system. If `_attr_name` is set, it overrides `_attr_translation_key` for determining the entity's name.
    *   `OverkizDescriptiveEntity` (used by sensor, button, number, select, binary_sensor) sets `self._attr_name` based on `description.name` (an English string from the `EntityDescription`) or `f"{self.device.label} {description.name}"` for sub-devices. This directly uses untranslated English strings or untranslatable device labels as part of the entity name.

2.  **Entities using `OverkizDescriptiveEntity` (e.g., sensor, button, number, select, binary_sensor)**:
    *   These entities define their names in their respective `EntityDescription` objects (e.g., `OverkizSensorDescription.name = "Battery level"` in `sensor.py`).
    *   `OverkizDescriptiveEntity` then assigns this hardcoded English string to `self._attr_name`. This bypasses the Home Assistant translation mechanism for the entity name itself.
    *   For example, in `sensor.py`: `SENSOR_DESCRIPTIONS` contains items like `OverkizSensorDescription(key=OverkizState.CORE_RSSI_LEVEL, name="RSSI level", ...)`. The resulting entity will be named "RSSI level" in English only.
    *   Some descriptions (e.g., in `select.py` or `sensor.py`) use a `translation_key` field, but this key is used for translating the *states* or *options* of the entity (e.g., enum members), not the entity's primary `name`.

3.  **Entities directly inheriting `OverkizEntity` (e.g., light, lock, cover, water_heater)**:
    *   These entities (e.g., `OverkizLight`, `OverkizLock`) generally do not set `_attr_name` in their own `__init__` methods, so it defaults to `None` (for non-sub-devices) or `self.device.label` (for sub-devices) from `OverkizEntity`.
    *   For non-sub-devices where `_attr_name` is `None`, Home Assistant will generate a name. However, if a specific, translatable entity name suffix (e.g., "Light", "Cover") is desired to be appended to the device name, this requires `_attr_translation_key`, which is missing for these.
    *   For sub-devices, `_attr_name` becomes `self.device.label`, which is not translated by Home Assistant.

4.  **Specific Hardcoded Names**:
    *   Some entities explicitly set `_attr_name` to a hardcoded English string.
        *   `cover/vertical_cover.py`: `LowSpeedCover` sets `self._attr_name = "Low speed"`.
        *   `sensor.py`: `OverkizHomeKitSetupCodeSensor` sets `self._attr_name = "HomeKit setup code"`.

5.  **Climate Entities**:
    *   Climate entity classes (e.g., `AtlanticElectricalTowelDryer` in `climate/atlantic_electrical_towel_dryer.py`) correctly set `_attr_translation_key = DOMAIN` (where `DOMAIN` is "overkiz").
    *   However, the `strings.json` file, under `entity.climate.overkiz`, is missing the required `"name": "..."` entry. It currently only defines `state_attributes`. This means that while a translation key is provided, the actual name translation is absent.

6.  **Info Box Exception Handling (for sensor, binary_sensor, number)**:
    *   The rule states: "If the entity's platform is either `binary_sensor`, `number`, `sensor`, or `update` and it has a device class set, and you want the entity to have the same name as the device class, you can omit the translation key because the entity will then automatically use the device class name."
    *   In `sensor.py`, for example, `OverkizSensorDescription(key=OverkizState.CORE_BATTERY_LEVEL, name="Battery level", device_class=SensorDeviceClass.BATTERY, ...)` has `name="Battery level"` which is different from the device class name ("Battery"). Thus, it would still require a translation key for "Battery level". If the desired name was just "Battery", then `name` in the description should be `None` (or not set to override) and `_attr_translation_key` also `None`.

The widespread use of hardcoded English strings in `EntityDescription.name` or direct `_attr_name` assignments, reliance on untranslatable `device.label` for entity names, and the missing `name` entry for climate translations mean the integration is not compliant.

## Suggestions

To make the `overkiz` integration compliant with the `entity-translations` rule:

1.  **Modify `OverkizDescriptiveEntity` and its `EntityDescription` variants:**
    *   In `entity.py`, `OverkizDescriptiveEntity` should prioritize `description.translation_key` to set `self._attr_translation_key`.
    *   The `name` attribute in `EntityDescription` objects (e.g., `OverkizSensorDescription`, `OverkizButtonDescription`) should be removed or set to `None` when `translation_key` is used for the entity name. The actual English name will then come from `strings.json`.
    *   `_attr_name` in `OverkizDescriptiveEntity` should generally remain `None` to allow the translation mechanism to work.
    *   For each `EntityDescription` that will use a `translation_key`:
        *   Add a `translation_key: str | None` field to the description dataclass.
        *   Populate `strings.json` with entries like:
            ```json
            // Example for a sensor
            "entity": {
              "sensor": {
                "my_sensor_translation_key": {
                  "name": "My Sensor Name in English"
                }
              }
            }
            ```
    *   **Handle the device class exception:** For `sensor`, `binary_sensor`, and `number` entities that have a `device_class` and where the intended entity name is the same as the (already translated) device class name:
        *   Set `description.translation_key = None` (or ensure it's not set).
        *   Ensure `_attr_name` remains `None` in the entity instance.
        *   `OverkizDescriptiveEntity` should not set `_attr_translation_key` if `description.translation_key` is `None`.

2.  **Modify `OverkizEntity` and direct inheritors (light, lock, cover, water_heater):**
    *   In `entity.py`, for `OverkizEntity`:
        *   When `self.is_sub_device` is true, `self._attr_name = self.device.label` should be reconsidered. If `device.label` (e.g., "Channel 1") is the full desired entity name and is inherently untranslatable by HA, this is problematic. A better approach for sub-entities might be to treat the `device.label` as part of the device identification and have a translatable entity type suffix (e.g., "Channel 1 Light", where "Light" is translated). This would involve `_attr_name = None` and setting `_attr_translation_key` for the sub-entity type.
        *   For non-sub-devices, `_attr_name` is already `None`, which is good.
    *   For entity classes like `OverkizLight`, `OverkizCover`, etc.:
        *   Set `_attr_translation_key` to a generic key for their platform (e.g., `_attr_translation_key = "light"` for lights).
        *   Add corresponding entries to `strings.json`:
            ```json
            // Example for light
            "entity": {
              "light": {
                "light": { // Assuming _attr_translation_key = "light"
                  "name": "Light"
                }
              }
            }
            ```
            This will result in names like "Device Name Light".

3.  **Address specific hardcoded `_attr_name` assignments:**
    *   `cover/vertical_cover.py`: For `LowSpeedCover`, change `self._attr_name = "Low speed"` to `self._attr_translation_key = "low_speed_cover"` and add to `strings.json`:
        ```json
        "entity": {
          "cover": {
            "low_speed_cover": {
              "name": "Low Speed"
            }
          }
        }
        ```
    *   `sensor.py`: For `OverkizHomeKitSetupCodeSensor`, change `self._attr_name = "HomeKit setup code"` to `self._attr_translation_key = "homekit_setup_code"` and add to `strings.json`:
        ```json
        "entity": {
          "sensor": {
            "homekit_setup_code": {
              "name": "HomeKit setup code"
            }
          }
        }
        ```

4.  **Fix Climate Entities:**
    *   Climate entity classes correctly set `_attr_translation_key = DOMAIN` (which evaluates to `"overkiz"`).
    *   In `strings.json`, add the `name` field to the `entity.climate.overkiz` section:
        ```json
        {
          "entity": {
            "climate": {
              "overkiz": {
                "name": "Climate Control", // Or "Thermostat", or a more generic term
                "state_attributes": {
                  // ... existing attribute translations
                }
              }
            }
            // ...
          }
        }
        ```
        If a more specific name than "Climate Control" is desired for different types of climate devices, then those specific climate classes would need to define their own unique `_attr_translation_key` and corresponding entries in `strings.json`.

By implementing these changes, entity names will be sourced from the standard Home Assistant translation system, making the integration more accessible to non-English speaking users.

_Created at 2025-05-28 12:39:06. Prompt tokens: 87044, Output tokens: 2633, Total tokens: 98376_
