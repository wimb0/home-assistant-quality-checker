```markdown
# samsungtv: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `icon-translations` rule requires integrations to define entity icons using `_attr_translation_key` and an `icons.json` file, rather than setting `_attr_icon` directly in the entity code or using dynamic logic. This integration provides `media_player` and `remote` entities, which should ideally define their icons using this mechanism.

Based on the provided code, the `samsungtv` integration does not currently implement icon translations.

1.  **Absence of `icons.json`:** The provided code files do not include an `icons.json` file within the `samsungtv` component directory (`homeassistant/components/samsungtv/icons.json`). This file is essential for defining icons via translation keys.
2.  **No `_attr_translation_key`:** Review of `homeassistant/components/samsungtv/entity.py`, `homeassistant/components/samsungtv/media_player.py`, and `homeassistant/components/samsungtv/remote.py` reveals that `_attr_translation_key` is not set on the entity base class (`SamsungTVEntity`), the `SamsungTVDevice` (media player), or the `SamsungTVRemote` entity.
3.  **Implicit Icons:** While `SamsungTVEntity` sets `_attr_has_entity_name = True` and `SamsungTVDevice` sets `_attr_device_class = MediaPlayerDeviceClass.TV`, which might provide default icons, the rule encourages using `icon-translations` for explicit control, especially for static icons (like the remote) or state-based icons (like mute on the media player). There is no explicit dynamic icon logic setting `_attr_icon` found in the code, which is good, but the icons are not defined via the preferred translation method either.

Because entities are defined that require icons, and the recommended method using `icons.json` and `_attr_translation_key` is not implemented, the integration does not follow the `icon-translations` rule.

## Suggestions

To comply with the `icon-translations` rule, the following steps should be taken:

1.  **Create `icons.json`:** Add a file named `icons.json` in the `homeassistant/components/samsungtv/` directory.
2.  **Add `_attr_translation_key`:**
    *   In `homeassistant/components/samsungtv/remote.py`, add `_attr_translation_key = "remote"` to the `SamsungTVRemote` class.
    *   In `homeassistant/components/samsungtv/media_player.py`, add `_attr_translation_key = "media_player"` to the `SamsungTVDevice` class.
3.  **Define Icons in `icons.json`:** Add the necessary entries in `icons.json` to define the icons for the entities.

    *   For the `remote` entity (which typically has a static icon):
        ```json
        {
          "entity": {
            "remote": {
              "remote": {
                "default": "mdi:remote"
              }
            }
          }
        }
        ```
    *   For the `media_player` entity, the device class `media_player.tv` provides a default icon. However, the media player might also need state-based icons, such as for the mute state. You can define this in `icons.json`:
        ```json
        {
          "entity": {
            "media_player": {
              "media_player": {
                "state": {
                   "on:is_volume_muted=true": "mdi:volume-mute",
                   "on:is_volume_muted=false": "mdi:volume-high"
                }
              }
            }
          }
        }
        ```
        *Note:* This example uses state attributes (`is_volume_muted`) to change the icon. If the device class provides suitable default icons for all states (like on/off and mute), you might choose not to override them to maintain consistency, but it's good practice to define the base entity icon via translation key. Defining the mute icon as shown above is a common pattern.

By implementing these changes, the integration will define its entity icons using the standard and preferred `icon-translations` method.

_Created at 2025-05-25 11:32:41. Prompt tokens: 30903, Output tokens: 1063, Total tokens: 32974_
