# samsungtv: entity-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [entity-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-translations)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The rule `entity-translations` requires that entities within an integration have translated names to improve accessibility for non-English speakers. This is typically achieved by setting `_attr_has_entity_name = True` and providing `_attr_translation_key` or by relying on automatic device class naming for specific platforms (binary_sensor, number, sensor, update) when a device class is set.

This integration implements a base entity `SamsungTVEntity` in `homeassistant/components/samsungtv/entity.py`. This base entity sets `_attr_has_entity_name = True`.

The two main entities derived from this base, `SamsungTVDevice` (media player) in `homeassistant/components/samsungtv/media_player.py` and `SamsungTVRemote` (remote) in `homeassistant/components/samsungtv/remote.py`, both set `_attr_name = None`.

When `_attr_has_entity_name` is `True` and `_attr_name` is `None`, Home Assistant automatically names the entity as the device name. The device name for this integration is derived from the `config_flow.py` which uses the `flow_title` defined in `homeassistant/components/samsungtv/strings.json`. The `flow_title` placeholder `{device}` is populated dynamically during the config flow, often using information like model name or IP, but critically, the `flow_title` itself *is* a translatable string defined in `strings.json`.

Since the primary entities (`media_player` and `remote`) represent the main interface for the device itself, having their names default to the translated device name is appropriate and fulfills the requirement that entity names are translated. The integration does not expose other specific sub-entities (like sensors for specific metrics or switches for specific functions) on the TV that would require their own distinct translated component names using `_attr_translation_key`.

Therefore, the integration correctly leverages the translated device name for its entities, satisfying the requirements of the `entity-translations` rule for the types of entities it creates.

## Suggestions

No suggestions needed.

_Created at 2025-05-25 11:32:05. Prompt tokens: 30178, Output tokens: 571, Total tokens: 32367_
