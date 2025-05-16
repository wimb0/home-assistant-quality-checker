# linkplay: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule mandates that all entities set the `_attr_has_entity_name = True` attribute. This allows Home Assistant to consistently and intelligently name entities. If an entity represents the main feature of a device, its `_attr_name` should be set to `None`, causing the entity to adopt the device's name. For other entities, `_attr_name` should be a descriptive string, which will then be prepended with the device name (e.g., "Device Name Sensor Name").

This rule applies to the `linkplay` integration as it defines entities.

The `linkplay` integration correctly follows this rule:

1.  **Base Entity Implementation:**
    The base class `LinkPlayBaseEntity` in `entity.py` correctly sets this attribute:
    ```python
    # entity.py
    class LinkPlayBaseEntity(Entity):
        """Representation of a LinkPlay base entity."""

        _attr_has_entity_name = True

        # ...
    ```
    All entities in the `linkplay` integration inherit from this base class, ensuring they all have `_attr_has_entity_name = True`.

2.  **Main Feature Entity (MediaPlayer):**
    The `LinkPlayMediaPlayerEntity` in `media_player.py` represents the primary functionality of a LinkPlay device. It correctly sets `_attr_name = None`, as recommended by the rule for main entities:
    ```python
    # media_player.py
    class LinkPlayMediaPlayerEntity(LinkPlayBaseEntity, MediaPlayerEntity):
        """Representation of a LinkPlay media player."""

        _attr_device_class = MediaPlayerDeviceClass.RECEIVER
        _attr_media_content_type = MediaType.MUSIC
        _attr_name = None  # Correct for main feature

        def __init__(self, bridge: LinkPlayBridge) -> None:
            """Initialize the LinkPlay media player."""
            super().__init__(bridge)
            # ...
    ```
    This means the media player entity will be named after the LinkPlay device itself (e.g., "Living Room Speaker").

3.  **Auxiliary Entities (Buttons):**
    The `LinkPlayButton` entities in `button.py` represent secondary functionalities (e.g., "Sync time", "Restart"). These entities inherit `_attr_has_entity_name = True` from `LinkPlayBaseEntity`. Their names are derived from their `entity_description` (either via `translation_key` or implicitly from `key` or `device_class`).
    For example, the "timesync" button:
    ```python
    # button.py
    BUTTON_TYPES: tuple[LinkPlayButtonEntityDescription, ...] = (
        LinkPlayButtonEntityDescription(
            key="timesync",
            translation_key="timesync", # Name comes from strings.json: "Sync time"
            # ...
        ),
        LinkPlayButtonEntityDescription(
            key="restart",
            device_class=ButtonDeviceClass.RESTART, # Name will be "Restart"
            # ...
        ),
    )

    class LinkPlayButton(LinkPlayBaseEntity, ButtonEntity):
        # ...
        def __init__(
            self,
            bridge: LinkPlayBridge,
            description: LinkPlayButtonEntityDescription,
        ) -> None:
            """Initialize LinkPlay button."""
            super().__init__(bridge)
            self.entity_description = description
            # _attr_name is implicitly set based on entity_description
            # ...
    ```
    This results in names like "Device Name Sync time" or "Device Name Restart", which is the desired behavior for non-main entities when `_attr_has_entity_name = True`.

The integration correctly implements `_attr_has_entity_name = True` for all its entities and appropriately uses `_attr_name = None` for its main entity type, while providing specific names for auxiliary entities.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:11:36. Prompt tokens: 11074, Output tokens: 1003, Total tokens: 14260_
