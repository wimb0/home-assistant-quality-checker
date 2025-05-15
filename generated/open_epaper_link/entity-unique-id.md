# open_epaper_link: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `entity-unique-id` rule requires that all entities provided by an integration have a unique ID. This ID must be unique per integration domain and per platform domain. This allows Home Assistant to track entities across restarts and enables users to customize them.

This rule applies to the `open_epaper_link` integration as it creates entities for sensors, buttons, cameras, select inputs, switches, and text inputs.

The integration correctly implements unique IDs for all its entities.

**Sensor Entities (`sensor.py`):**
*   `OpenEPaperLinkTagSensor`: Sets `self._attr_unique_id = f"{tag_mac}_{description.key}"`. `tag_mac` is the unique MAC address of the ESL tag, and `description.key` is unique for each sensor type (e.g., "temperature", "battery_voltage") associated with that tag. This ensures a unique ID.
*   `OpenEPaperLinkAPSensor`: Sets `self._attr_unique_id = f"{self._hub.entry.entry_id}_{description.key}"`. `self._hub.entry.entry_id` is the unique ID of the config entry (and since this integration is `single_config_entry: true`, this is effectively a singleton identifier for the AP). `description.key` is unique for each sensor type for the AP (e.g., "ip", "wifi_ssid"). This ensures a unique ID.

**Button Entities (`button.py`):**
*   Tag-specific buttons (e.g., `ClearPendingTagButton`, `ForceRefreshButton`, `RebootTagButton`, `ScanChannelsButton`, `DeepSleepButton`): These set `self._attr_unique_id` using a format like `f"{tag_mac}_clear_pending"`. `tag_mac` is unique, and the suffix (e.g., `_clear_pending`) is unique for that button type on that tag. This is correct.
*   AP-specific buttons (`RebootAPButton`, `RefreshTagTypesButton`): These set `self._attr_unique_id` to a fixed string, e.g., `"reboot_ap"` or `"refresh_tag_types"`. Given that `open_epaper_link` is a `single_config_entry` integration (as per `manifest.json`), there is only one AP device. Thus, these fixed strings are unique for these specific buttons associated with the single AP device within this integration. This is an acceptable implementation for single config entry integrations.

**Camera Entities (`camera.py`):**
*   `EPDCamera`: Sets `self._attr_unique_id = f"{tag_mac}_content"`. `tag_mac` is unique, and `_content` is a fixed suffix for the camera entity of that tag. This is correct.

**Select Entities (`select.py`):**
*   `APConfigSelect` (and `APTimeHourSelect` which inherits its `__init__` logic for unique ID): Sets `self._attr_unique_id = f"{hub.entry.entry_id}_{key}"`. `hub.entry.entry_id` is unique for the config entry, and `key` (e.g., "channel", "led", "sleeptime1") is unique for each select entity type. This is correct.

**Switch Entities (`switch.py`):**
*   `APConfigSwitch`: Sets `self._attr_unique_id = f"{hub.entry.entry_id}_{key}"`. `hub.entry.entry_id` is unique for the config entry, and `key` (e.g., "preview", "ble") is unique for each switch entity type. This is correct.

**Text Entities (`text.py`):**
*   `APConfigText`: Sets `self._attr_unique_id = f"{hub.entry.entry_id}_{key}"`. `hub.entry.entry_id` is unique for the config entry, and `key` (e.g., "alias", "repo") is unique for each AP text entity type. This is correct.
*   `TagNameText`: Sets `self._attr_unique_id = f"{tag_mac}_alias"`. `tag_mac` is unique, and `_alias` is a fixed suffix for the alias text entity of that tag. This is correct.

All entities consistently use the `_attr_unique_id` attribute to set their unique IDs, following the recommended pattern of combining a device-specific unique part (MAC address or config entry ID) with an entity-type-specific key.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 20:37:07. Prompt tokens: 60391, Output tokens: 1142, Total tokens: 63423_
