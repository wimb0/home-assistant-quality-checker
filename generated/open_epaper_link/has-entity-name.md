# open_epaper_link: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **done**                                       |
| Reason | N/A |

## Overview

The `has-entity-name` rule requires that all entities within an integration set the `_attr_has_entity_name = True` attribute. This allows Home Assistant to consistently format entity names, typically as "Device Name Entity Specific Name" or just "Device Name" if the entity represents the primary feature of the device (in which case `_attr_name` would be `None`).

This rule applies to the `open_epaper_link` integration as it creates several entities across different platforms (sensor, button, camera, select, switch, text).

The integration **fully follows** this rule. All entity classes defined in the integration consistently set `_attr_has_entity_name = True`.

Specifically:

1.  **Sensor Entities (`sensor.py`):**
    *   `OpenEPaperLinkTagSensor`: Sets `self._attr_has_entity_name = True` (line 451). It uses `self._attr_translation_key = description.key` to provide the specific part of the name.
    *   `OpenEPaperLinkAPSensor`: Sets `self._attr_has_entity_name = True` (line 569). It also uses `self._attr_translation_key = description.key`.

2.  **Button Entities (`button.py`):**
    *   `ClearPendingTagButton`: Sets `self._attr_has_entity_name = True` (line 129).
    *   `ForceRefreshButton`: Sets `self._attr_has_entity_name = True` (line 176).
    *   `RebootTagButton`: Sets `self._attr_has_entity_name = True` (line 223).
    *   `ScanChannelsButton`: Sets `self._attr_has_entity_name = True` (line 270).
    *   `DeepSleepButton`: Sets `self._attr_has_entity_name = True` (line 317).
    *   `RebootAPButton`: Sets `self._attr_has_entity_name = True` (line 362).
    *   `RefreshTagTypesButton`: Sets `self._attr_has_entity_name = True` (line 404).
    *   All button entities use `self._attr_translation_key` to provide the specific part of their names.

3.  **Camera Entities (`camera.py`):**
    *   `EPDCamera`: Sets `self._attr_has_entity_name = True` (line 105). It uses `self._attr_translation_key = "content"` for the specific name part.

4.  **Select Entities (`select.py`):**
    *   `APConfigSelect`: Sets `self._attr_has_entity_name = True` (line 143). It uses `self._attr_translation_key = key`.
    *   `APTimeHourSelect`: Inherits from `APConfigSelect` and thus also correctly implements `_attr_has_entity_name = True` and uses a translation key.

5.  **Switch Entities (`switch.py`):**
    *   `APConfigSwitch`: Sets `self._attr_has_entity_name = True` (line 60). It uses `self._attr_translation_key = key`.

6.  **Text Entities (`text.py`):**
    *   `APConfigText`: Sets `self._attr_has_entity_name = True` (line 52). It uses `self._attr_translation_key = key`.
    *   `TagNameText`: Sets `self._attr_has_entity_name = True` (line 126). It uses `self._attr_translation_key = "tag_alias"`.

In all cases, the entities use `_attr_translation_key` in conjunction with `_attr_has_entity_name = True`. This is a standard Home Assistant practice that allows for translatable entity names while adhering to the naming convention promoted by the `has-entity-name` rule (i.e., "Device Name + Specific Entity Name"). No entities in this integration appear to represent the sole primary feature of a device that would warrant `_attr_name = None`.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 20:37:55. Prompt tokens: 60577, Output tokens: 1087, Total tokens: 65586_
