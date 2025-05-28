# overkiz: has-entity_name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule requires all entities defined by an integration to set the `_attr_has_entity_name = True` attribute. This allows Home Assistant to consistently manage entity naming, typically by combining a device name with an entity-specific name, or using the device name if the entity represents the main feature.

This rule applies to the `overkiz` integration as it registers multiple entities across various platforms (sensor, light, switch, cover, climate, etc.).

The `overkiz` integration largely adheres to this rule through its base entity classes:
*   `homeassistant/components/overkiz/entity.py`:
    *   The `OverkizEntity` class correctly sets `_attr_has_entity_name = True` and initializes `_attr_name` to `None`. For sub-devices, it sets `_attr_name` to `self.device.label`, which is appropriate for providing a specific name part for the sub-entity.
    *   The `OverkizDescriptiveEntity` class, inheriting from `OverkizEntity`, also correctly uses `_attr_has_entity_name = True`. It sets `_attr_name` based on the `EntityDescription.name` provided, or a combination of `self.device.label` and `description.name` for sub-devices. If `description.name` is not provided (i.e., is `None`) and it's not a sub-device, `_attr_name` correctly remains `None`, indicating it might be a main feature of the device.

Most entities within the `overkiz` integration (e.g., sensors, switches, lights, covers, climate devices, water heaters, locks, binary sensors, buttons, numbers, selects, sirens) inherit from one of these base classes and thus correctly implement the `has-entity-name` mechanism.

However, one entity type does not follow the rule:
*   `homeassistant/components/overkiz/scene.py`:
    The `OverkizScene` class inherits directly from Home Assistant's `Scene` base class. It sets an `_attr_name` but does **not** set `_attr_has_entity_name = True`.
    ```python
    # homeassistant/components/overkiz/scene.py
    class OverkizScene(Scene):
        """Representation of an Overkiz Scene."""

        def __init__(self, scenario: Scenario, client: OverkizClient) -> None:
            """Initialize the scene."""
            self.scenario = scenario
            self.client = client
            self._attr_name = self.scenario.label # _attr_has_entity_name is missing
            self._attr_unique_id = self.scenario.oid
    ```
    While `OverkizScene` entities might not be associated with a Home Assistant `device_info` (and thus the device name prepending logic might not apply), the rule "Entities use `has_entity_name = True`" is stated without exceptions related to device association. For consistency and to explicitly adhere to the rule, this attribute should be set.

Due to `OverkizScene` not setting `_attr_has_entity_name = True`, the integration does not fully follow the rule.

## Suggestions

To make the `overkiz` integration fully compliant with the `has-entity-name` rule, the `OverkizScene` class should be updated.

1.  **Modify `OverkizScene` in `homeassistant/components/overkiz/scene.py`:**
    Add the `_attr_has_entity_name = True` attribute to the `OverkizScene` class.

    **Example Code Change:**
    ```python
    # homeassistant/components/overkiz/scene.py

    from __future__ import annotations

    from typing import Any

    from pyoverkiz.client import OverkizClient
    from pyoverkiz.models import Scenario

    from homeassistant.components.scene import Scene # Keep this import
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from . import OverkizDataConfigEntry


    async def async_setup_entry(
        hass: HomeAssistant,
        entry: OverkizDataConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up the Overkiz scenes from a config entry."""
        data = entry.runtime_data

        async_add_entities(
            OverkizScene(scene, data.coordinator.client) for scene in data.scenarios
        )


    class OverkizScene(Scene):
        """Representation of an Overkiz Scene."""

        _attr_has_entity_name = True  # Add this line

        def __init__(self, scenario: Scenario, client: OverkizClient) -> None:
            """Initialize the scene."""
            self.scenario = scenario
            self.client = client
            self._attr_name = self.scenario.label
            self._attr_unique_id = self.scenario.oid
            # If Overkiz scenes are not device-bound, _attr_device_info would typically not be set.
            # If they are considered to belong to the hub/gateway device, _attr_device_info
            # could be set accordingly, but this is outside the scope of just the has-entity-name rule.

        async def async_activate(self, **kwargs: Any) -> None:
            """Activate the scene."""
            await self.client.execute_scenario(self.scenario.oid)
    ```

**Why this change satisfies the rule:**
By adding `_attr_has_entity_name = True` to `OverkizScene`, all entity types defined by the `overkiz` integration will comply with the rule's requirement. Even if a scene entity does not have an associated `device_info` (meaning `device_name` is not available for prepending), setting this attribute ensures the integration is explicitly following the prescribed pattern for entity naming configuration. The resulting name for such an entity would effectively be its `_attr_name`.

_Created at 2025-05-28 12:13:02. Prompt tokens: 87088, Output tokens: 1498, Total tokens: 95796_
