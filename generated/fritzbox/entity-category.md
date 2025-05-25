```markdown
# fritzbox: entity-category

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [entity-category](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-category)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `entity-category` rule requires entities to be assigned an appropriate `EntityCategory` (like `DIAGNOSTIC` or `CONFIG`) if their default category is inappropriate (i.e., they are not primary operational entities). This rule is applicable to the `fritzbox` integration as it creates various types of entities.

The `fritzbox` integration correctly applies `EntityCategory.DIAGNOSTIC` to several sensor and binary sensor entities that report diagnostic information such as battery status (`binary_sensor.py`, `sensor.py`), lock status (`binary_sensor.py`), and thermostat details like comfort/eco temperatures and scheduling information (`sensor.py`). It also correctly handles the primary temperature sensor category based on device capabilities (`sensor.py`). Primary entities like switches, covers, lights, and the main climate entity correctly do not have an `EntityCategory` set, which aligns with the rule.

However, the `button.py` file defines `FritzBoxTemplate` entities, which are buttons that apply predefined templates configured on the FRITZ!Box. These are typically configuration or utility actions rather than primary operational controls. Such entities should generally be assigned `EntityCategory.CONFIG`. The current implementation of `FritzBoxTemplate` does not assign any `EntityCategory`.

Because there is at least one entity type that should have an `EntityCategory` assigned according to standard Home Assistant conventions but currently does not, the integration does not fully follow the rule.

## Suggestions

To comply with the `entity-category` rule, the `FritzBoxTemplate` entity in `button.py` should be assigned the `EntityCategory.CONFIG`.

Here's how the `FritzBoxTemplate` class in `homeassistant/components/fritzbox/button.py` could be modified:

```python
class FritzBoxTemplate(FritzBoxEntity, ButtonEntity):
    """Interface between FritzhomeTemplate and hass."""

    _attr_entity_category = EntityCategory.CONFIG # Add this line

    @property
    def data(self) -> FritzhomeTemplate:
        """Return the template data entity."""
        return self.coordinator.data.templates[self.ain]

    # ... rest of the class ...
```

Adding this attribute will correctly classify the template buttons as configuration entities in the Home Assistant UI, improving the user experience, especially in auto-generated dashboards and entity lists.

_Created at 2025-05-25 11:35:58. Prompt tokens: 18700, Output tokens: 624, Total tokens: 20429_
