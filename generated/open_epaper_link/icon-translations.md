# open_epaper_link: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `icon-translations` rule requires that custom icons for entities are defined in an `icons.json` file, referenced by a `_attr_translation_key` in the entity's Python code, rather than being set directly via `_attr_icon` or `entity_description.icon`. This helps to centralize icon definitions and allows for more complex icon logic, like state-dependent icons, through the translation system.

This rule applies to the `open_epaper_link` integration as it defines multiple entities (sensors, switches, buttons, text inputs, select entities) that use custom icons.

The integration currently does **NOT** fully follow this rule.
While most entities (Sensor, Switch, Button, Text, Select) set the `_attr_translation_key` attribute, they also set their icons directly in Python code using `entity_description.icon` (for Sensors) or `self._attr_icon` (for Switch, Button, Text, Select). Furthermore, the `homeassistant/components/open_epaper_link/icons.json` file is missing the necessary `entity` section to provide the actual icon translations for these keys. The existing `icons.json` only defines icons for services.

**Specific Code References:**

1.  **Missing `entity` icon definitions in `icons.json`:**
    The current `homeassistant/components/open_epaper_link/icons.json` file only contains a `services` key:
    ```json
    {
      "services": {
        "dlimg": {
          "service": "mdi:download"
        },
        // ... other services
      }
    }
    ```
    It lacks the required `entity` section where icons for sensors, switches, etc., should be defined based on their `translation_key`.

2.  **Sensors (`sensor.py`):**
    *   Entities like `OpenEPaperLinkAPSensor` and `OpenEPaperLinkTagSensor` use `OpenEPaperLinkSensorEntityDescription`.
    *   `OpenEPaperLinkSensorEntityDescription` defines an `icon: str` attribute, which is used to set the icon directly (e.g., `icon="mdi:ip"` for the "ip" sensor).
    *   The sensor classes set `self._attr_translation_key = description.key`.
    *   **Issue:** `_attr_translation_key` is set, but the icon is also defined in Python via `description.icon`, and the `icons.json` file lacks the corresponding entries (e.g., `entity.sensor.ip`).

3.  **Switches (`switch.py`):**
    *   `APConfigSwitch` sets `self._attr_icon = icon` directly in its `__init__` method.
    *   It also sets `self._attr_translation_key = key`.
    *   **Issue:** Similar to sensors, `_attr_icon` is set directly, `_attr_translation_key` is set, but `icons.json` is missing `entity.switch.<key>` definitions.

4.  **Buttons (`button.py`):**
    *   All button classes (e.g., `ClearPendingTagButton`, `RebootAPButton`) set `self._attr_icon` directly.
    *   They also set `self._attr_translation_key`.
    *   **Issue:** Icons are set directly, `_attr_translation_key` is used, but `icons.json` is missing `entity.button.<key>` definitions.

5.  **Text Inputs (`text.py`):**
    *   `APConfigText` and `TagNameText` set `self._attr_icon` directly.
    *   They also set `self._attr_translation_key`.
    *   **Issue:** Icons are set directly, `_attr_translation_key` is used, but `icons.json` is missing `entity.text.<key>` definitions.

6.  **Select Entities (`select.py`):**
    *   `APConfigSelect` (and `APTimeHourSelect` which inherits its icon handling) sets `self._attr_icon = icon` directly.
    *   It also sets `self._attr_translation_key = key`.
    *   **Issue:** Icons are set directly, `_attr_translation_key` is used, but `icons.json` is missing `entity.select.<key>` definitions.

The `camera.py` entities do not set a custom icon and rely on the default camera icon, so they are not in violation of this specific rule regarding custom icon setting.

The primary issue is that icon definitions are still in Python code, and the `icons.json` file is not utilized for entity icons as intended by the `icon-translations` rule, despite `_attr_translation_key` being set.

## Suggestions

To make the `open_epaper_link` integration compliant with the `icon-translations` rule, the following changes are recommended:

1.  **Update `icons.json`:**
    Add an `entity` section to `homeassistant/components/open_epaper_link/icons.json`. This section should contain sub-sections for each entity platform that uses custom icons (`sensor`, `switch`, `button`, `text`, `select`).

    Example structure for `icons.json`:
    ```json
    {
      "entity": {
        "sensor": {
          "ip": {
            "default": "mdi:ip"
          },
          "wifi_ssid": {
            "default": "mdi:wifi-settings"
          },
          "temperature": {
            "default": "mdi:thermometer"
          }
          // ... other sensor translation keys and their default icons
        },
        "switch": {
          "preview": {
            "default": "mdi:eye"
          },
          "ble": {
            "default": "mdi:bluetooth"
          }
          // ... other switch translation keys
        },
        "button": {
          "clear_pending": {
            "default": "mdi:broom"
          },
          "reboot_ap": {
            "default": "mdi:restart"
          }
          // ... other button translation keys
        },
        "text": {
          "alias": { // For APConfigText with key "alias"
            "default": "mdi:rename-box"
          },
          "tag_alias": { // For TagNameText
            "default": "mdi:rename"
          }
          // ... other text translation keys
        },
        "select": {
          "channel": {
            "default": "mdi:wifi"
          },
          "led": {
            "default": "mdi:brightness-5"
          }
          // ... other select translation keys
        }
      },
      "services": {
        // ... existing service icon definitions ...
      }
    }
    ```
    Populate this with all the translation keys used in the Python code and their corresponding MDI icons that are currently hardcoded.

2.  **Remove Direct Icon Assignments in Python:**
    For all entities that now have their icons defined in `icons.json` via `_attr_translation_key`:
    *   **Sensors (`sensor.py`):** Remove the `icon: str` field from `OpenEPaperLinkSensorEntityDescription` if the icon is to be solely determined by `_attr_translation_key`. If `OpenEPaperLinkSensorEntityDescription` is used elsewhere or if some sensors might not use translations, this needs careful consideration. However, for those using `_attr_translation_key`, the icon should come from `icons.json`.
        Alternatively, if `entity_description.icon` is kept as a fallback, ensure it's clear that the primary source is `icons.json`. The rule implies `icons.json` is the source when `_attr_translation_key` is used.
    *   **Switches (`switch.py`):** Remove `self._attr_icon = icon` from `APConfigSwitch.__init__`.
    *   **Buttons (`button.py`):** Remove `self._attr_icon = "..."` from all button classes' `__init__` methods.
    *   **Text Inputs (`text.py`):** Remove `self._attr_icon = icon` (or hardcoded icon) from `APConfigText.__init__` and `TagNameText.__init__`.
    *   **Select Entities (`select.py`):** Remove `self._attr_icon = icon` from `APConfigSelect.__init__`.

    The icon should be resolved by Home Assistant Core using the `_attr_translation_key` to look up the definition in `icons.json`.

3.  **Verify Device Class Icons:**
    The rule states: "Be aware that entities can also get icons from the device class. If the context of the entity is exactly the same as the device class, we should not overwrite this icon to maintain consistency between integrations."
    Review entities that have a `device_class` set (e.g., `sensor.temperature` with `SensorDeviceClass.TEMPERATURE`).
    *   If the icon specified in Python (and subsequently moved to `icons.json`) is the same as the default icon for that device class, consider removing the `_attr_translation_key` for that specific entity and letting the device class provide the icon. This simplifies the configuration.
    *   If the icon is intentionally different from the device class's default for a good reason, then using `_attr_translation_key` and `icons.json` is the correct approach.

By making these changes, the `open_epaper_link` integration will correctly use the icon translation system, centralizing its entity icon definitions in `icons.json` and adhering to the quality scale rule.

_Created at 2025-05-14 21:05:16. Prompt tokens: 60544, Output tokens: 2308, Total tokens: 66090_
