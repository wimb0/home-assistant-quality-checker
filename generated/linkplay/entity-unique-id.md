# linkplay: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unique-id` rule requires that all entities created by an integration have a unique ID. This allows Home Assistant to track entities across restarts, enabling customizations like renaming or changing units of measurement.

This rule applies to the `linkplay` integration as it creates entities for `button` and `media_player` platforms.

The `linkplay` integration correctly implements unique IDs for its entities:

1.  **Media Player Entities (`media_player.py`):**
    The `LinkPlayMediaPlayerEntity` class sets its unique ID in the `__init__` method:
    ```python
    # media_player.py
    class LinkPlayMediaPlayerEntity(LinkPlayBaseEntity, MediaPlayerEntity):
        # ...
        def __init__(self, bridge: LinkPlayBridge) -> None:
            """Initialize the LinkPlay media player."""

            super().__init__(bridge)
            self._attr_unique_id = bridge.device.uuid  # <-- Unique ID set here
            # ...
    ```
    The `bridge.device.uuid` is expected to be a unique identifier for each LinkPlay device, thus ensuring a unique ID for each media player entity.

2.  **Button Entities (`button.py`):**
    The `LinkPlayButton` class also sets its unique ID in the `__init__` method:
    ```python
    # button.py
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
            self._attr_unique_id = f"{bridge.device.uuid}-{description.key}"  # <-- Unique ID set here
    ```
    Here, the unique ID is a combination of the `bridge.device.uuid` and `description.key` (e.g., "timesync", "restart"). This ensures that different buttons associated with the same device also have unique IDs.

Both entity types use the `_attr_unique_id` attribute as recommended, and the chosen identifiers are appropriate for ensuring uniqueness per integration domain and per platform domain.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:10:53. Prompt tokens: 10330, Output tokens: 627, Total tokens: 12138_
