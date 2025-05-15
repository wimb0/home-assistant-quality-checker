# open_epaper_link: entity-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [entity-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-translations` rule requires that entities provide translated names to improve accessibility for non-English speaking users. This is typically achieved by setting `_attr_has_entity_name = True` and `_attr_translation_key` on the entity, and then providing the corresponding translations in the `strings.json` file under the `entity.<platform>.<translation_key>.name` path.

This rule applies to the `open_epaper_link` integration as it creates entities for multiple platforms, including `sensor`, `button`, `camera`, `select`, `switch`, and `text`.

The integration correctly implements the Python side of this requirement:
*   All entity classes (e.g., `OpenEPaperLinkTagSensor`, `OpenEPaperLinkAPSensor` in `sensor.py`; `APConfigSwitch` in `switch.py`; `EPDCamera` in `camera.py`; `APConfigSelect` in `select.py`; `TagNameText` in `text.py`; various button classes in `button.py`) set `_attr_has_entity_name = True`.
*   These classes also set an `_attr_translation_key`. For example:
    *   In `sensor.py`, `OpenEPaperLinkTagSensor` uses `self._attr_translation_key = description.key`.
    *   In `button.py`, `ClearPendingTagButton` uses `self._attr_translation_key = "clear_pending"`.
    *   In `camera.py`, `EPDCamera` uses `self._attr_translation_key = "content"`.
    *   In `select.py`, `APConfigSelect` uses `self._attr_translation_key = key`.
    *   In `switch.py`, `APConfigSwitch` uses `self._attr_translation_key = key`.
    *   In `text.py`, `APConfigText` uses `self._attr_translation_key = key` and `TagNameText` uses `self._attr_translation_key = "tag_alias"`.

However, the integration does **not** fully follow the rule because its `strings.json` file is missing the required translations for these entities. The current `homeassistant/components/open_epaper_link/strings.json` file only contains translations for the configuration flow:
```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "host": "[%key:common::config_flow::data::host%]"
        }
      }
    }
  }
}
```
It lacks the necessary `entity` section where translations for entity names should be defined. For example, for a sensor with `_attr_translation_key = "ip"`, the `strings.json` file should contain an entry like `entity.sensor.ip.name = "IP Address"`.

## Suggestions

To make the `open_epaper_link` integration compliant with the `entity-translations` rule, the `strings.json` file needs to be updated to include translations for all entities.

1.  **Modify `strings.json`:**
    Add an `entity` top-level key. Under this key, add sub-keys for each platform (`sensor`, `button`, `camera`, `select`, `switch`, `text`).

2.  **Add Translation Entries:**
    For each entity defined in the Python code, identify its `_attr_translation_key`. Then, add a corresponding entry in `strings.json`. The English name provided in the entity description dataclasses (e.g., `name` field in `OpenEPaperLinkSensorEntityDescription`) or hardcoded in entity setup should be used as the default English translation.

    Here's an example structure for `strings.json`:
    ```json
    {
      "config": {
        "step": {
          "user": {
            "data": {
              "host": "[%key:common::config_flow::data::host%]"
            }
          }
        }
      },
      "entity": {
        "sensor": {
          "ip": {
            "name": "IP Address"
          },
          "wifi_ssid": {
            "name": "WiFi SSID"
          },
          "record_count": {
            "name": "Tag count"
          },
          "temperature": {
            "name": "Temperature"
          },
          "battery_voltage": {
            "name": "Battery Voltage"
          },
          "battery_percentage": {
            "name": "Battery Percentage"
          }
          // ... Add all other sensor translation keys from AP_SENSOR_TYPES and TAG_SENSOR_TYPES
        },
        "button": {
          "clear_pending": {
            "name": "Clear Pending"
          },
          "force_refresh": {
            "name": "Force Refresh"
          },
          "reboot_tag": {
            "name": "Reboot Tag"
          },
          "scan_channels": {
            "name": "Scan Channels"
          },
          "deep_sleep": {
            "name": "Deep Sleep"
          },
          "reboot_ap": {
            "name": "Reboot AP"
          },
          "refresh_tag_types": {
            "name": "Refresh Tag Types"
          }
        },
        "camera": {
          "content": {
            "name": "Content"
          }
        },
        "select": {
          "channel": {
            "name": "IEEE 802.15.4 channel"
          },
          "led": {
            "name": "RGB LED brightness"
          },
          "tft": {
            "name": "TFT brightness"
          },
          "maxsleep": {
            "name": "Maximum Sleep"
          },
          "lock": {
            "name": "Lock tag inventory"
          },
          "wifipower": {
            "name": "Wifi power"
          },
          "language": {
            "name": "Language"
          },
          "discovery": {
            "name": "Discovery Method"
          },
          "subghzchannel": {
            "name": "Sub-GHz channel"
          },
          "sleeptime1": {
            "name": "No updates between 1 (from)"
          },
          "sleeptime2": {
            "name": "No updates between 2 (to)"
          }
          // ... Add all other select translation keys from SELECT_ENTITIES and APTimeHourSelect
        },
        "switch": {
          "preview": {
            "name": "Preview Images"
          },
          "ble": {
            "name": "Bluetooth"
          },
          "nightlyreboot": {
            "name": "Nightly Reboot"
          },
          "showtimestamp": {
            "name": "Show Timestamp"
          }
          // ... Add all other switch translation keys from SWITCH_ENTITIES
        },
        "text": {
          "alias": {
            "name": "Alias"
          },
          "repo": {
            "name": "Repository"
          },
          "tag_alias": {
            "name": "Tag Alias" 
          }
          // ... Add all other text translation keys
        }
      }
    }
    ```

    **Note:** The `name` values in the example above (e.g., "IP Address", "Clear Pending") should be derived from the `name` attribute in the `OpenEPaperLinkSensorEntityDescription` (for sensors), or the `name` specified in the `SWITCH_ENTITIES`, `SELECT_ENTITIES`, `AP_TEXT_ENTITIES` lists, or the implied name for other entities (e.g., "Content" for camera, "Alias" for tag alias text entity). The `_attr_has_entity_name = True` setting ensures that the device name will be prepended automatically by Home Assistant, so the translations in `strings.json` should only contain the specific name of the entity itself (e.g., "IP Address", not "Device Name IP Address").

By adding these translations to `strings.json`, the integration will fully comply with the `entity-translations` rule, allowing entity names to be translated into different languages.

_Created at 2025-05-14 21:02:56. Prompt tokens: 60533, Output tokens: 2008, Total tokens: 67077_
