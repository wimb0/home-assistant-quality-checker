```markdown
# fritzbox: entity-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [entity-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-translations)                                                     |
| Status | **todo**                                                                 |

## Overview

The `entity-translations` rule requires that all entities have translated names to support international users. This is primarily achieved by setting `_attr_has_entity_name = True` and providing an `_attr_translation_key` that points to a name defined in the `strings.json` file. An exception exists for certain platforms (`binary_sensor`, `number`, `sensor`, `update`) if a `device_class` is set and the intended name matches the device class name, in which case the `_attr_translation_key` can be omitted.

The `fritzbox` integration provides entities across multiple platforms: `binary_sensor`, `button`, `climate`, `cover`, `light`, `sensor`, and `switch`.

Based on the code review:

*   **`binary_sensor.py`** and **`sensor.py`**: These platforms define entities using `EntityDescription` subclasses (`FritzBinarySensorEntityDescription` and `FritzSensorEntityDescription`). The base `FritzBoxEntity` class (in `entity.py`) correctly sets `_attr_has_entity_name = True` when an `entity_description` is provided. The entity descriptions for these platforms consistently use either a `translation_key` pointing to a name in `strings.json` (e.g., `alarm`, `holiday_active` for binary sensors; `comfort_temperature`, `eco_temperature` for sensors) or rely on the `device_class` exemption (e.g., `battery_low` binary sensor; `temperature`, `humidity`, `battery`, `power_consumption`, etc. sensors). These entities appear to follow the rule or its exemption.
*   **`climate.py`**, **`cover.py`**, **`light.py`**, **`switch.py`**, and **`button.py`**: These platform entities (`FritzboxThermostat`, `FritzboxCover`, `FritzboxLight`, `FritzboxSwitch`, `FritzBoxTemplate`) do *not* use an `EntityDescription` when calling the base `FritzBoxEntity.__init__`. In this case, `FritzBoxEntity.__init__` sets `_attr_name = self.data.name` (using the name from the FRITZ!Box API for the device or template) and does *not* set `_attr_has_entity_name = True`. This behavior results in entities named based on the device/template name from the API (e.g., "My Device Cover", "My Light", "My Template Button") rather than the preferred "Device Name Translated Entity Name" pattern achieved with `_attr_has_entity_name = True` and `_attr_translation_key`.
    *   The `climate` entity (`FritzboxThermostat`) *does* set `_attr_translation_key = "thermostat"`, but since `_attr_has_entity_name` is not set to `True`, this key is not used for the primary entity name.
    *   The `cover`, `light`, `switch`, and `button` entities do not set any `_attr_translation_key`.

Because the `climate`, `cover`, `light`, `switch`, and `button` entities do not follow the modern `_attr_has_entity_name = True` + `_attr_translation_key` pattern for their entity names, the integration does not fully comply with the `entity-translations` rule.

## Suggestions

To make the `fritzbox` integration compliant with the `entity-translations` rule, the following changes are suggested:

1.  **Modify the base `FritzBoxEntity.__init__` (Optional but Recommended):**
    Consider removing the `else` block in `FritzBoxEntity.__init__` that sets `_attr_name = self.data.name` when `entity_description` is `None`. This base class should ideally not be setting the entity name directly based on API data.

2.  **Update Platform Entity Classes:**
    For the entity classes that do not use an `EntityDescription` (`FritzboxThermostat`, `FritzboxCover`, `FritzboxLight`, `FritzboxSwitch`, `FritzBoxTemplate`), explicitly set `_attr_has_entity_name = True` and an appropriate `_attr_translation_key`.

    *   **`climate.py`**: Add `_attr_has_entity_name = True` to `FritzboxThermostat`. The `_attr_translation_key = "thermostat"` is already present.

        ```diff
        --- a/homeassistant/components/fritzbox/climate.py
        +++ b/homeassistant/components/fritzbox/climate.py
        @@ -54,6 +54,7 @@
     _attr_precision = PRECISION_HALVES
     _attr_temperature_unit = UnitOfTemperature.CELSIUS
     _attr_translation_key = "thermostat"
        +    _attr_has_entity_name = True

         def __init__(
             self,

        ```

    *   **`cover.py`**: Add `_attr_has_entity_name = True` and `_attr_translation_key = "cover"` to `FritzboxCover`.

        ```diff
        --- a/homeassistant/components/fritzbox/cover.py
        +++ b/homeassistant/components/fritzbox/cover.py
        @@ -29,6 +29,8 @@
 
     _attr_device_class = CoverDeviceClass.BLIND
     _attr_supported_features = (
        +    _attr_has_entity_name = True
        +    _attr_translation_key = "cover"
         CoverEntityFeature.OPEN
         | CoverEntityFeature.SET_POSITION
         | CoverEntityFeature.CLOSE

        ```

    *   **`light.py`**: Add `_attr_has_entity_name = True` and `_attr_translation_key = "light"` to `FritzboxLight`.

        ```diff
        --- a/homeassistant/components/fritzbox/light.py
        +++ b/homeassistant/components/fritzbox/light.py
        @@ -26,6 +26,8 @@
 class FritzboxLight(FritzBoxDeviceEntity, LightEntity):
     """The light class for FRITZ!SmartHome lightbulbs."""
 
+    _attr_has_entity_name = True
+    _attr_translation_key = "light"
     def __init__(
         self,
         coordinator: FritzboxDataUpdateCoordinator,

        ```

    *   **`switch.py`**: Add `_attr_has_entity_name = True` and `_attr_translation_key = "switch"` to `FritzboxSwitch`.

        ```diff
        --- a/homeassistant/components/fritzbox/switch.py
        +++ b/homeassistant/components/fritzbox/switch.py
        @@ -19,6 +19,8 @@
 
 class FritzboxSwitch(FritzBoxDeviceEntity, SwitchEntity):
     """The switch class for FRITZ!SmartHome switches."""
+    _attr_has_entity_name = True
+    _attr_translation_key = "switch"
 
     @property
     def is_on(self) -> bool:

        ```

    *   **`button.py`**: Add `_attr_has_entity_name = True` and `_attr_translation_key = "template"` to `FritzBoxTemplate`. (Using "template" as the key seems appropriate for this entity type).

        ```diff
        --- a/homeassistant/components/fritzbox/button.py
        +++ b/homeassistant/components/fritzbox/button.py
        @@ -19,6 +19,8 @@
 
 class FritzBoxTemplate(FritzBoxEntity, ButtonEntity):
     """Interface between FritzhomeTemplate and hass."""
+    _attr_has_entity_name = True
+    _attr_translation_key = "template"
 
     @property
     def data(self) -> FritzhomeTemplate:

        ```

3.  **Add Missing Translations to `strings.json`:**
    Add the corresponding `name` entries for the new translation keys under the respective platforms in `homeassistant/components/fritzbox/strings.json`.

    ```diff
    --- a/homeassistant/components/fritzbox/strings.json
    +++ b/homeassistant/components/fritzbox/strings.json
    @@ -40,6 +40,11 @@
       "climate": {
         "thermostat": {
           "state_attributes": {
    +        "preset_mode": {
    +          "name": "[%key:component::climate::entity_component::_::state_attributes::preset_mode::name%]",
    +          "state": {
    +            "eco": "[%key:component::climate::entity_component::_::state_attributes::preset_mode::state::eco%]",
    +            "comfort": "[%key:component::climate::entity_component::_::state_attributes::preset_mode::state::comfort%]",
    +            "holiday": "Holiday",
    +            "summer": "Summer"
             "preset_mode": {
               "name": "[%key:component::climate::entity_component::_::state_attributes::preset_mode::name%]",
               "state": {
    @@ -50,6 +55,20 @@
           }
         }
       },
    +    "cover": {
    +      "cover": { "name": "Cover" }
    +    },
    +    "light": {
    +      "light": { "name": "Light" }
    +    },
    +    "switch": {
    +      "switch": { "name": "Switch" }
    +    },
    +    "button": {
    +      "template": { "name": "Template" }
    +    },
+        "eco": "[%key:component::climate::entity_component::_::state_attributes::preset_mode::state::eco%]",
+        "comfort": "[%key:component::climate::entity_component::_::state_attributes::preset_mode::state::comfort%]",
+        "holiday": "Holiday",
+        "summer": "Summer"
+      }
+    }
+  },
+  "cover": {
+    "cover": { "name": "Cover" }
+  },
+  "light": {
+    "light": { "name": "Light" }
+  },
+  "switch": {
+    "switch": { "name": "Switch" }
+  },
+  "button": {
+    "template": { "name": "Template" }
+  },
       "sensor": {
         "comfort_temperature": { "name": "Comfort temperature" },
         "eco_temperature": { "name": "Eco temperature" },

    ```

By implementing these changes, the `climate`, `cover`, `light`, `switch`, and `button` entities will adopt the modern naming pattern, combining the device/template name with a translated entity type, ensuring better support for users in different languages.
```

_Created at 2025-05-25 11:36:59. Prompt tokens: 19035, Output tokens: 2656, Total tokens: 27255_
