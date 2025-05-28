```markdown
# pegel_online: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **done**                                                                 |

## Overview

The `has-entity-name` rule requires entities to set the `_attr_has_entity_name` attribute to `True` to improve naming consistency and clarity when entities are associated with devices.

This rule applies to the `pegel_online` integration as it creates sensor entities linked to devices representing measurement stations.

The `pegel_online` integration follows this rule. The base entity class `PegelOnlineEntity`, located in `homeassistant/components/pegel_online/entity.py`, sets `_attr_has_entity_name = True` on line 16. All platform entities, such as the sensors defined in `homeassistant/components/pegel_online/sensor.py`, inherit from this base class, thereby inheriting `_attr_has_entity_name = True`.

Furthermore, the sensor entities are defined using `SensorEntityDescription` instances that include a `translation_key`. With `_attr_has_entity_name = True` and a `translation_key` set, Home Assistant automatically generates entity names using the pattern "[Device Name] [Entity Name]", where the Entity Name comes from the translated string for the `translation_key`. Looking at `homeassistant/components/pegel_online/strings.json`, the sensor translation keys have corresponding `name` entries, fulfilling this pattern.

The integration does not have a single primary entity that represents the sole function of the device, so setting `_attr_name = None` is not applicable or necessary here. The current naming convention is appropriate for the different types of measurements provided by the station device.

## Suggestions

No suggestions needed. The integration correctly implements the requirements of the `has-entity-name` rule.
```

_Created at 2025-05-25 11:22:26. Prompt tokens: 5984, Output tokens: 484, Total tokens: 7414_
