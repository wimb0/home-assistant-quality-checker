# overkiz: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `icon-translations` rule requires that custom icons for entities are defined in an `icons.json` file and referenced via a translation key, rather than being set directly in Python code. This helps to centralize icon definitions and supports features like state-based icons.

The `overkiz` integration **applies** to this rule as it defines custom icons for several of its entities.

The integration partially follows the rule:
*   **Compliance:**
    *   An `icons.json` file (`homeassistant/components/overkiz/icons.json`) exists.
    *   **Climate Entities:** Icons for `preset_mode` state attributes of climate entities are correctly defined in `icons.json`. Climate entities (e.g., `AtlanticElectricalTowelDryer`) set `_attr_translation_key = "overkiz"`, and the `icons.json` file has a corresponding `climate.overkiz.state_attributes.preset_mode` section.
    *   **Select Entities:** Icons for select entities are correctly defined in `icons.json`. `OverkizSelectDescription` instances use `translation_key` (e.g., `"open_closed_pedestrian"`), and `icons.json` contains corresponding entries like `select.open_closed_pedestrian` which define default and state-specific icons. This works because `EntityDescription.translation_key` is used for icon translation if `EntityDescription.icon` is not set.

*   **Non-Compliance:**
    1.  **Direct `_attr_icon` Usage:**
        *   The `OverkizHomeKitSetupCodeSensor` entity in `homeassistant/components/overkiz/sensor.py` directly sets its icon using `_attr_icon = "mdi:shield-home"`.
            ```python
            # homeassistant/components/overkiz/sensor.py
            class OverkizHomeKitSetupCodeSensor(OverkizEntity, SensorEntity):
                _attr_icon = "mdi:shield-home" 
                # ...
            ```
    2.  **Direct Icon Assignment via `EntityDescription`:**
        *   Multiple entity types (Sensor, Number, Switch, Button, Binary Sensor) that inherit from `OverkizDescriptiveEntity` receive their icons directly from an `icon` attribute within their respective `EntityDescription` subclass (e.g., `OverkizSensorDescription`, `OverkizNumberDescription`).
        *   For example, in `homeassistant/components/overkiz/sensor.py`:
            ```python
            # homeassistant/components/overkiz/sensor.py
            @dataclass(frozen=True)
            class OverkizSensorDescription(SensorEntityDescription):
                # ...
                native_value: Callable[[OverkizStateType], StateType] | None = None
                # 'icon' is inherited from SensorEntityDescription but populated here
            
            SENSOR_DESCRIPTIONS: list[OverkizSensorDescription] = [
                OverkizSensorDescription(
                    key=OverkizState.CORE_BATTERY,
                    name="Battery",
                    icon="mdi:battery", # Icon set directly in description
                    device_class=SensorDeviceClass.ENUM,
                    translation_key="battery", # Used for string translations
                    # ...
                ),
                # ... many other similar descriptions ...
            ]
            ```
            This pattern is repeated in:
            *   `homeassistant/components/overkiz/number.py` with `OverkizNumberDescription`.
            *   `homeassistant/components/overkiz/switch.py` with `OverkizSwitchDescription`.
            *   `homeassistant/components/overkiz/button.py` with `OverkizButtonDescription`.
            *   `homeassistant/components/overkiz/binary_sensor.py` with `OverkizBinarySensorDescription`.

These direct icon assignments bypass the `icons.json` mechanism for the main entity icon. While many of these descriptions also have a `translation_key` (used for string translations), this key is not currently being used for icon translation for these specific icons because the `icon` attribute in the description takes precedence.

Entities related to `cover`, `lock`, `siren`, and most `water_heater` platforms do not appear to set custom icons directly and likely rely on device class icons or default Home Assistant icons, which is acceptable.

Because some entities set icons directly in Python code, the integration does not fully follow the `icon-translations` rule.

## Suggestions

To make the `overkiz` integration compliant with the `icon-translations` rule, the following changes are recommended:

1.  **For `OverkizHomeKitSetupCodeSensor` (in `homeassistant/components/overkiz/sensor.py`):**
    *   Remove the direct assignment: `_attr_icon = "mdi:shield-home"`.
    *   Set a translation key for the entity: `_attr_translation_key = "homekit_setup_code"`.
    *   Add a corresponding entry to `homeassistant/components/overkiz/icons.json`:
        ```json
        {
          "entity": {
            "sensor": {
              // ... other sensor entries ...
              "homekit_setup_code": {
                "default": "mdi:shield-home"
              }
            }
          }
        }
        ```

2.  **For entities using `OverkizDescriptiveEntity` (Sensor, Number, Switch, Button, Binary Sensor):**
    *   **Modify `EntityDescription` Subclasses:**
        *   For `OverkizSensorDescription`, `OverkizNumberDescription`, `OverkizSwitchDescription`, `OverkizButtonDescription`, and `OverkizBinarySensorDescription`, ensure the `icon` field is not populated in the description instances where a custom icon is desired. The `icon` attribute should ideally be removed from these dataclass definitions if it's not inherited and always meant to be translated. If inherited (e.g. from `SensorEntityDescription`), simply do not assign a value to it in the `overkiz` specific description instances.
    *   **Utilize `translation_key`:**
        *   Ensure that each `EntityDescription` instance has an appropriate `translation_key` set. This key is often already present for string translations (e.g., `translation_key="battery"` for the battery sensor). This same key will be used for icon translation.
    *   **Update `icons.json`:**
        *   For each entity that previously had an icon defined in its Python description, add a corresponding entry in `homeassistant/components/overkiz/icons.json`. The path in `icons.json` will be `entity.<platform>.<translation_key>`.

    *   **Example for a Sensor (e.g., `CORE_BATTERY` sensor):**
        *   **Current Python (`sensor.py`):**
            ```python
            OverkizSensorDescription(
                key=OverkizState.CORE_BATTERY,
                name="Battery",
                icon="mdi:battery", // To be removed
                device_class=SensorDeviceClass.ENUM,
                translation_key="battery",
                # ...
            )
            ```
        *   **Proposed Python (`sensor.py`):**
            ```python
            OverkizSensorDescription(
                key=OverkizState.CORE_BATTERY,
                name="Battery",
                // icon="mdi:battery", // Removed
                device_class=SensorDeviceClass.ENUM,
                translation_key="battery",
                # ...
            )
            ```
        *   **Proposed `icons.json` addition:**
            ```json
            {
              "entity": {
                "sensor": {
                  "battery": { // Corresponds to translation_key="battery"
                    "default": "mdi:battery"
                    // If state-specific icons are needed for this sensor:
                    // "state": {
                    //   "low": "mdi:battery-low",
                    //   "critical": "mdi:battery-alert"
                    // }
                  },
                  // ... other sensor icon translations ...
                }
              }
            }
            ```
    *   This process should be repeated for all custom icons defined in `OverkizNumberDescription`, `OverkizSwitchDescription`, `OverkizButtonDescription`, and `OverkizBinarySensorDescription`.

By making these changes, all custom icons will be managed through `icons.json`, adhering to the `icon-translations` rule. This approach leverages the existing `translation_key` mechanism already used for string translations, promoting consistency. If an entity's icon should be determined by its `device_class`, then no `translation_key` for icon purposes or `icon` attribute in the description is needed, and no entry in `icons.json` would be required for that specific entity's main icon.

_Created at 2025-05-28 12:41:39. Prompt tokens: 87769, Output tokens: 2116, Total tokens: 96503_
