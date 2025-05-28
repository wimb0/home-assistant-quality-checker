# fritzbox: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that all entities created by the integration have a unique ID set, registered with Home Assistant's entity registry. This unique ID must be unique per integration domain and per platform domain. The purpose is to allow users to customize entities and ensure they persist across restarts.

The `fritzbox` integration applies to this rule as it creates various types of entities (binary sensors, climates, covers, lights, sensors, switches, buttons) dynamically based on discovered devices and templates from a FRITZ!Box router.

The integration follows this rule. It utilizes a base entity class `FritzBoxEntity` defined in `homeassistant/components/fritzbox/entity.py`. The `__init__` method of this class is responsible for setting the `_attr_unique_id`:

```python
class FritzBoxEntity(CoordinatorEntity[FritzboxDataUpdateCoordinator], ABC):
    """Basis FritzBox entity."""

    def __init__(
        self,
        coordinator: FritzboxDataUpdateCoordinator,
        ain: str,
        entity_description: EntityDescription | None = None,
    ) -> None:
        """Initialize the FritzBox entity."""
        super().__init__(coordinator)

        self.ain = ain
        if entity_description is not None:
            self._attr_has_entity_name = True
            self.entity_description = entity_description
            self._attr_unique_id = f"{ain}_{entity_description.key}"
        else:
            self._attr_name = self.data.name
            self._attr_unique_id = ain
```

This base class implements the required logic:
1.  If an `entity_description` is provided (common for platforms like sensors and binary sensors where a single device can expose multiple entities of the same platform type, distinguished by a `key`), the unique ID is set to `f"{ain}_{entity_description.key}"`. The AIN (actor identification number) is the unique identifier provided by the FRITZ!Box for a device or template. Combining the AIN with the description key ensures the unique ID is unique per device and entity type/characteristic.
2.  If no `entity_description` is provided, the unique ID is set directly to the `ain`. This is used for platforms where a device typically exposes only one entity of that specific platform type (e.g., a device is either a thermostat or not, a switch or not, etc.). In these cases (like climate, cover, light, switch, and button for templates), the AIN alone is sufficient to ensure uniqueness per device, and thus unique per integration domain (`fritzbox`) and platform domain (e.g., `light`, `switch`).

Specific platforms use this base class correctly:
*   `binary_sensor.py` and `sensor.py` pass an `entity_description` containing a unique `key`, resulting in unique IDs like `ain_temperature` or `ain_alarm`.
*   `climate.py`, `cover.py`, `light.py`, and `switch.py` do not pass an `entity_description` to the base `FritzBoxEntity` constructor, resulting in unique IDs set to the device's `ain`. As explained, this is sufficient because a single device AIN uniquely identifies the single entity of that platform type on the device.
*   `button.py` for templates also uses the base class without an entity description, setting the unique ID to the template's `ain`. Since AINs are unique across templates, this also results in unique IDs for button entities.

The integration also includes migration logic in `__init__.py` (`_update_unique_id`) which handles updating historical unique ID formats for temperature sensors and binary sensors to match the `ain_suffix` pattern now established, further indicating the correct implementation of unique IDs.

All dynamic entities examined correctly set the `_attr_unique_id` property using a scheme that guarantees uniqueness per integration domain and platform domain, fulfilling the rule's requirement.

## Suggestions

No suggestions needed. The integration successfully follows the `entity-unique-id` rule.

_Created at 2025-05-25 11:20:23. Prompt tokens: 18893, Output tokens: 1005, Total tokens: 22299_
