```markdown
# pegel_online: entity-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [entity-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-translations) |
| Status | **done**                                                                 |

## Overview

This rule requires that entities created by the integration have translated names to improve usability for non-English speakers. This is typically achieved by setting `_attr_has_entity_name = True` on the entity and providing a `_attr_translation_key` that references a name defined in the integration's `strings.json` file. The rule also notes that for sensor, binary_sensor, number, and update entities with a device class set, the `translation_key` can be omitted, and the entity will use the translated device class name.

The `pegel_online` integration fully follows this rule.

1.  **Base Entity (`entity.py`):** The base class `PegelOnlineEntity` sets `_attr_has_entity_name = True`, indicating that entities derived from it will derive their name from a combination of the device name and the entity's own name part (from translation key or device class). The device name is correctly set to include the station name and water name.
2.  **Sensor Entity Descriptions (`sensor.py`):** The `SENSORS` tuple in `sensor.py` defines the various sensors provided by the integration using `SensorEntityDescription`. Each description includes a `key` and, for almost all entries, a `translation_key` (e.g., `air_temperature`, `clearance_height`, `water_level`). Some descriptions also specify a `device_class`.
3.  **`strings.json`:** The `strings.json` file contains entity name definitions under the `"entity": { "sensor": { ... } }` key, matching the `translation_key` values used in `sensor.py`. For example, `"air_temperature": { "name": "Air temperature" }` provides the English name that will be used in combination with the device name.
4.  **Device Class Fallback:** The `ph_value` sensor description in `sensor.py` has a `device_class` (`SensorDeviceClass.PH`) but no `translation_key`. As noted in the rule, for sensor entities with a device class, the translated device class name ("pH" in this case) is automatically used as the entity name when `translation_key` is omitted. This correctly implements the allowed fallback mechanism.

By setting `_attr_has_entity_name = True`, utilizing `translation_key`s pointing to `strings.json` entries, and correctly using the device class fallback mechanism, the integration ensures its entities have names that can be translated, adhering to the rule's requirements.

## Suggestions

No suggestions needed. The integration correctly implements the `entity-translations` rule.
```

_Created at 2025-05-25 11:25:07. Prompt tokens: 5940, Output tokens: 682, Total tokens: 7826_
