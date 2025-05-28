```markdown
# samsungtv: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule requires entities to utilize the `_attr_has_entity_name = True` attribute. This attribute, combined with a set `_attr_name`, allows Home Assistant to construct consistent entity names using the device name as a prefix (e.g., "My Device Temperature"). The rule specifies that the primary entity representing the device's main function should set `_attr_name = None`, resulting in the entity simply using the device's name. This rule has no exceptions and applies to all entities created by an integration.

This integration fully follows the `has-entity-name` rule. The base class `SamsungTVEntity`, defined in `homeassistant/components/samsungtv/entity.py`, sets `_attr_has_entity_name = True` on line 41.

Both entities derived from this base class, `SamsungTVDevice` (media_player, `homeassistant/components/samsungtv/media_player.py`, line 54) and `SamsungTVRemote` (remote, `homeassistant/components/samsungtv/remote.py`, line 21), set `_attr_name = None`.

Given that a Samsung TV primarily acts as a media player and can be controlled via a remote, both platforms can be considered main features of the device. Setting `_attr_name = None` for these entities is consistent with the rule's guidance for main feature entities.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:28:39. Prompt tokens: 30222, Output tokens: 444, Total tokens: 31640_
