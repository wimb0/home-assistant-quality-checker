# wled: entity-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [entity-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-translations)                                                     |
| Status | **todo**                                       |
| Reason | N/A |

## Overview

The `entity-translations` rule requires that entities have translated names, typically by setting `_attr_has_entity_name = True`, providing an `_attr_translation_key`, and including the corresponding translation in the integration's `translations/<lang>.json` (or `strings.json`) file. An exception exists for `binary_sensor`, `number`, `sensor`, and `update` platforms: if they have a `device_class` set and the desired name is the device class name, `_attr_translation_key` can be omitted.

The `wled` integration defines a base entity `WLEDEntity` in `entity.py` which correctly sets `_attr_has_entity_name = True`. Most entities in the integration correctly use `_attr_translation_key` and have corresponding entries in `translations/en.json`.

However, there are two entities that do not fully comply:

1.  **`WLEDUpdateEntity` (`update.py`):**
    *   This entity sets `_attr_title = "WLED"`. When `_attr_has_entity_name` is `True`, `_attr_title` directly provides the entity name suffix, bypassing `_attr_translation_key` and device class based naming. This results in a hardcoded, non-translated English name "WLED".
    *   It has `_attr_device_class = UpdateDeviceClass.FIRMWARE`. According to the rule's exception, if the desired name were "Firmware", `_attr_title` could be removed, and the entity would use the core-translated name for this device class. If "WLED" is the desired name, it should be translated via `_attr_translation_key`.

2.  **`WLEDRestartButton` (`button.py`):**
    *   This entity sets `_attr_device_class = ButtonDeviceClass.RESTART` but does not set an explicit `_attr_translation_key`.
    *   The `ButtonEntity` base class will use the `device_class` value ("restart") as the `translation_key`.
    *   The `wled` integration's `translations/en.json` file does not contain an entry for `entity.button.restart.name`.
    *   While Home Assistant core provides a translation for the "restart" button device class, the `entity-translations` rule's exception for omitting `_attr_translation_key` (and relying on device class naming) explicitly lists only `binary_sensor`, `number`, `sensor`, and `update` platforms. Since `button` is not in this list, it implies that `button` entities should provide their translations within the integration, even if the name matches the device class.

Due to these two entities, the integration does not fully follow the `entity-translations` rule.

## Suggestions

To make the `wled` integration compliant with the `entity-translations` rule, the following changes are recommended:

1.  **For `WLEDUpdateEntity` (`update.py`):**

    Choose one of the following approaches:

    *   **Option A: Use the device class name ("Firmware").** This is the simplest if "Firmware" is an acceptable name.
        *   Remove the line `_attr_title = "WLED"`.
        *   The entity will automatically use the name "Firmware" (associated with `UpdateDeviceClass.FIRMWARE`), which is translated by Home Assistant core. This is compliant as `update` entities fall under the rule's exception.

    *   **Option B: Use a custom translated name (e.g., "WLED" or "Device Update").**
        *   Remove the line `_attr_title = "WLED"`.
        *   Set an appropriate translation key:
            ```python
            # In WLEDUpdateEntity class
            self._attr_translation_key = "firmware_update"  # Or any other descriptive key
            ```
        *   Add the corresponding translation to `translations/en.json` (and other language files if any):
            ```json
            // In translations/en.json
            {
              "entity": {
                "update": {
                  "firmware_update": { // Must match the _attr_translation_key
                    "name": "WLED" // Or "Device Update", "Firmware", etc.
                  }
                  // ... other update entity translations if any
                }
                // ... other platforms
              }
            }
            ```

2.  **For `WLEDRestartButton` (`button.py`):**

    To ensure the "Restart" button name is translated via the integration's own translation files:

    *   Explicitly set the `_attr_translation_key`. Using the device class value as the key is common:
        ```python
        # In WLEDRestartButton class
        # constructor (__init__)
        super().__init__(coordinator=coordinator)
        self._attr_translation_key = "restart" # Matches ButtonDeviceClass.RESTART.value
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_restart"
        ```
        Alternatively, use a more specific key if desired, e.g., `self._attr_translation_key = "device_restart"`.

    *   Add the corresponding translation to `translations/en.json` (and other language files if any):
        ```json
        // In translations/en.json
        {
          "entity": {
            "button": {
              "restart": { // Must match the _attr_translation_key
                "name": "Restart"
              }
              // ... other button entity translations if any
            }
            // ... other platforms
          }
        }
        ```
        If you chose a specific key like `device_restart`, use that key in the JSON file.

By implementing these changes, all entities in the `wled` integration will have properly translated names according to the `entity-translations` rule.

_Created at 2025-05-10 23:03:08. Prompt tokens: 21549, Output tokens: 1452, Total tokens: 30218_
