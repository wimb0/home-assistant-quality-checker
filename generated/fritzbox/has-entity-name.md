```markdown
# fritzbox: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule applies to this integration as it creates entities that represent devices and their features. The rule requires that entities use the `_attr_has_entity_name = True` attribute to improve naming consistency.

The integration partially follows the rule:

1.  Entities created using an `EntityDescription` (like `binary_sensor.py` and `sensor.py`) correctly inherit `_attr_has_entity_name = True` from the base class `FritzBoxEntity` when an `entity_description` is provided during initialization. Their names are correctly formed using the device name and the entity description's name/translation key. This aligns with the rule's first requirement.
2.  However, entities representing the main feature of a device (e.g., `switch`, `cover`, `light`) and template entities (`button`) do **not** provide an `entity_description` when initializing the `FritzBoxEntity` base class (e.g., `FritzboxSwitch(coordinator, ain)` in `switch.py`, `FritzboxCover(coordinator, ain)` in `cover.py`, `FritzboxLight(coordinator, ain)` in `light.py`, `FritzBoxTemplate(coordinator, ain)` in `button.py`). In this case, the `FritzBoxEntity` base class (in `entity.py`) sets `self._attr_name = self.data.name` and does **not** explicitly set `self._attr_has_entity_name = True` (it defaults to `False`).

The rule's second requirement states that for the main feature of a device, `_attr_has_entity_name` should be `True` and `_attr_name` should be `None`. The integration currently achieves the desired entity naming outcome (just the device name) for these main entities by setting `_attr_name = self.data.name` while `_attr_has_entity_name` is `False`. This contradicts the required mechanism laid out by the rule.

Therefore, the integration needs to be updated to use the `_attr_has_entity_name = True` and `_attr_name = None` pattern for entities representing the main device feature.

## Suggestions

To comply with the `has-entity-name` rule, modify the `FritzBoxEntity` base class in `homeassistant/components/fritzbox/entity.py` as follows:

1.  Always set `_attr_has_entity_name = True` in the `__init__` method.
2.  Set `_attr_name = None` when `entity_description` is not provided.

```python
# homeassistant/components/fritzbox/entity.py
...
class FritzBoxEntity(CoordinatorEntity[FritzboxDataUpdateCoordinator], ABC):
    """Basis FritzBox entity."""

    # Always set has_entity_name = True
    _attr_has_entity_name = True # Add this line here

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
            # _attr_has_entity_name is already True from class attribute
            self.entity_description = entity_description
            self._attr_unique_id = f"{ain}_{entity_description.key}"
            # _attr_name will be derived from entity_description.name/translation_key
        else:
            # For main entities, set _attr_name to None
            self._attr_name = None # Change this line
            self._attr_unique_id = ain

...
```

This change ensures that all entities created via `FritzBoxEntity` have `_attr_has_entity_name = True`. For entities without an `EntityDescription`, setting `_attr_name = None` will instruct Home Assistant to use the device name as the entity name, achieving the desired result ("My Device") using the mechanism required by the rule. Entities with an `EntityDescription` will continue to get their name derived from the description key combined with the device name ("My Device Temperature").

_Created at 2025-05-25 11:20:35. Prompt tokens: 19079, Output tokens: 1072, Total tokens: 21785_
