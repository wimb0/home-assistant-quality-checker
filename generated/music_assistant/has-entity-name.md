# music_assistant: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **done**                                                                 |

## Overview

The `has-entity-name` rule requires entities to set the `_attr_has_entity_name = True` attribute. This allows Home Assistant to generate more consistent and user-friendly entity names based on the device name and the entity's specific function.

This rule applies to the `music_assistant` integration because it creates `media_player` entities.

The `music_assistant` integration **fully follows** this rule.

1.  **Base Entity Class Sets `_attr_has_entity_name = True`**:
    The base entity class for this integration, `MusicAssistantEntity`, located in `homeassistant/components/music_assistant/entity.py`, correctly sets `_attr_has_entity_name = True`:
    ```python
    # homeassistant/components/music_assistant/entity.py
    class MusicAssistantEntity(Entity):
        """Base Entity from Music Assistant Player."""

        _attr_has_entity_name = True  # Rule requirement met
        _attr_should_poll = False
        # ...
    ```
    All entities created by this integration, including `MusicAssistantPlayer`, inherit this attribute.

2.  **Main Entity Naming (`MusicAssistantPlayer`)**:
    The `MusicAssistantPlayer` entity, defined in `homeassistant/components/music_assistant/media_player.py`, represents the primary functionality of a Music Assistant player device. This class sets `_attr_name = None`:
    ```python
    # homeassistant/components/music_assistant/media_player.py
    class MusicAssistantPlayer(MusicAssistantEntity, MediaPlayerEntity):
        """Representation of MediaPlayerEntity from Music Assistant Player."""

        _attr_name = None  # Indicates entity name should be the device name
        _attr_media_image_remotely_accessible = True
        # ...
    ```
    According to the `has-entity-name` rule documentation, when `_attr_has_entity_name = True` and `_attr_name = None`, the entity's name will be the same as the device's name. This is the recommended approach for an entity that represents the main feature of a device.

    The device name itself is set in the `MusicAssistantEntity`'s `__init__` method using `self.player.display_name`:
    ```python
    # homeassistant/components/music_assistant/entity.py
    # class MusicAssistantEntity(Entity):
        # ...
        def __init__(self, mass: MusicAssistantClient, player_id: str) -> None:
            # ...
            self._attr_device_info = DeviceInfo(
                # ...
                name=self.player.display_name, # This is the device name
                # ...
            )
    ```
    Therefore, a `MusicAssistantPlayer` entity will adopt the `display_name` of the Music Assistant player it represents (e.g., if the device is "Kitchen Speaker", the entity will also be named "Kitchen Speaker"). This aligns perfectly with the rule's intent for clear and consistent naming.

The integration correctly implements `_attr_has_entity_name = True` and utilizes the naming conventions promoted by this rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:03:14. Prompt tokens: 30203, Output tokens: 826, Total tokens: 34048_
