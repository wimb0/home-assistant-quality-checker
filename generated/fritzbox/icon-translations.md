```markdown
# fritzbox: icon-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [icon-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/icon-translations)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `icon-translations` rule requires integrations to define icons using `icons.json` and `translation_key` or rely on icons provided by `device_class` or domain defaults, rather than setting `_attr_icon` directly in the entity code.

This integration fully follows the rule.

The analysis of the provided code reveals the following:

*   **`icons.json` usage:** The integration includes an `icons.json` file (`homeassistant/components/fritzbox/icons.json`). This file defines state-based icons for specific binary sensors (`holiday_active`, `summer_active`, `window_open`) and state-attribute-based icons for climate preset modes (`holiday`, `summer`).
*   **`translation_key` usage:** Several entities, particularly binary sensors and sensors defined using entity descriptions (`FritzBinarySensorEntityDescription` and `FritzSensorEntityDescription`) in `binary_sensor.py` and `sensor.py`, utilize the `translation_key` attribute (e.g., `translation_key="alarm"`, `translation_key="holiday_active"`, `translation_key="comfort_temperature"`). This correctly links the entity to translations, including icon translations defined in `icons.json` or `strings.json`.
*   **Reliance on `device_class` and domain defaults:** Many entities (e.g., cover, switch, various sensors like temperature, humidity, power) have their icons determined by their `device_class` or the entity domain type. For example, the `FritzboxCover` in `cover.py` sets `_attr_device_class = CoverDeviceClass.BLIND`. The `FritzboxSwitch` in `switch.py` does not set `_attr_icon` or `_attr_translation_key`, relying on the default switch icon. Sensors like `temperature`, `humidity`, `power_consumption` use standard device classes (`SensorDeviceClass.TEMPERATURE`, `SensorDeviceClass.HUMIDITY`, `SensorDeviceClass.POWER`) which provide default icons.
*   **Absence of `_attr_icon`:** No instances of `_attr_icon` being set directly on entity classes or instances were found across the platform files (`binary_sensor.py`, `cover.py`, `switch.py`, `sensor.py`, `light.py`, `button.py`).

Based on this, the integration successfully uses the recommended patterns (`icons.json`, `translation_key`, `device_class`, domain defaults) for icon handling.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:37:26. Prompt tokens: 19760, Output tokens: 669, Total tokens: 21467_
