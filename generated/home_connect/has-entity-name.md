# home_connect: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **todo**                                                                 |

## Overview

The `has-entity-name` rule requires that all entities set the `_attr_has_entity_name = True` attribute. This allows Home Assistant to consistently manage entity naming by combining the device name with an entity-specific name. If the entity-specific name (`_attr_name`) is set to `None`, the entity will simply use the device name, which is suitable for an entity representing the main feature of a device.

This rule applies to the `home_connect` integration as it creates various entities.

The integration generally follows this rule, as the base class `HomeConnectEntity` (in `entity.py`) correctly sets `_attr_has_entity_name = True`:
```python
# entity.py
class HomeConnectEntity(CoordinatorEntity[HomeConnectCoordinator]):
    """Generic Home Connect entity (base class)."""

    _attr_has_entity_name = True
    # ...
```
Most entities within the `home_connect` integration inherit from `HomeConnectEntity` (or `HomeConnectOptionEntity` which also inherits it) and thus correctly have `_attr_has_entity_name = True` by default. These entities typically provide their entity-specific name via their `EntityDescription` (e.g., through `translation_key` or `name`).

However, there is one exception:
The `HomeConnectProgramSwitch` class in `switch.py` explicitly overrides this attribute to `False` and constructs its own full name:
```python
# switch.py
class HomeConnectProgramSwitch(HomeConnectEntity, SwitchEntity):
    # ...
    def __init__(
        self,
        coordinator: HomeConnectCoordinator,
        appliance: HomeConnectApplianceData,
        program: EnumerateProgram,
    ) -> None:
        # ...
        desc = " ".join(["Program", program.key.split(".")[-1]])
        if appliance.info.type == "WasherDryer":
            desc = " ".join(
                ["Program", program.key.split(".")[-3], program.key.split(".")[-1]]
            )
        self.program = program
        super().__init__(
            coordinator,
            appliance,
            SwitchEntityDescription(
                key=EventKey.BSH_COMMON_ROOT_ACTIVE_PROGRAM, # Note: This key is not unique per program instance
                entity_registry_enabled_default=False,
            ),
        )
        self._attr_name = f"{appliance.info.name} {desc}" # Manually constructs full name
        self._attr_unique_id = f"{appliance.info.ha_id}-{desc}"
        self._attr_has_entity_name = False # Violation of the rule
```
This direct setting of `_attr_has_entity_name = False` and manual concatenation of the device name (`appliance.info.name`) into `_attr_name` violates the `has-entity-name` rule, which mandates `_attr_has_entity_name = True` for consistent name handling by the core.

It is noted that `HomeConnectProgramSwitch` entities are deprecated and scheduled for removal in Home Assistant version 2025.6.0 (as indicated by repair issues created by the integration). However, the `has-entity-name` rule does not list exceptions for deprecated entities.

The integration does not currently make use of the `_attr_name = None` pattern (in conjunction with `_attr_has_entity_name = True`) to designate a "main" entity that would only use the device name. While this pattern is a good practice for main features, its absence is not a direct violation of the core requirement that "Entities use `has_entity_name = True`."

Due to `HomeConnectProgramSwitch` setting `_attr_has_entity_name = False`, the integration does not fully follow the rule.

## Suggestions

To make the `home_connect` integration fully compliant with the `has-entity-name` rule, the `HomeConnectProgramSwitch` class in `switch.py` should be updated.

1.  **Ensure `_attr_has_entity_name` is `True`**:
    *   Remove the line `self._attr_has_entity_name = False`. This will allow it to inherit `_attr_has_entity_name = True` from the `HomeConnectEntity` base class.

2.  **Provide only the entity-specific name via `_attr_name` or `EntityDescription`**:
    *   The `_attr_name` should contain only the entity-specific part of the name (e.g., "Program Eco50"), not the device name combined with the entity-specific part. Home Assistant will automatically prepend the device name when `_attr_has_entity_name` is `True`.

    A more robust way to handle this, aligning with the structure of `HomeConnectEntity`, would be to pass a more specific `EntityDescription` to the `super().__init__` call.

    **Proposed Change for `HomeConnectProgramSwitch` in `switch.py`:**
    ```python
    class HomeConnectProgramSwitch(HomeConnectEntity, SwitchEntity):
        # _attr_has_entity_name = True is inherited from HomeConnectEntity

        def __init__(
            self,
            coordinator: HomeConnectCoordinator,
            appliance: HomeConnectApplianceData,
            program: EnumerateProgram,
        ) -> None:
            """Initialize the entity."""
            # Construct the entity-specific name part (e.g., "Program Eco50")
            entity_specific_name_part = " ".join(["Program", program.key.split(".")[-1]])
            if appliance.info.type == "WasherDryer":
                entity_specific_name_part = " ".join(
                    ["Program", program.key.split(".")[-3], program.key.split(".")[-1]]
                )
            
            self.program = program # Keep this instance variable

            # Create an EntityDescription with the specific program key and entity-specific name
            # Using program.key for EntityDescription.key ensures a stable and unique key part.
            entity_description = SwitchEntityDescription(
                key=program.key,  # Use the actual program key for the description
                name=entity_specific_name_part, # This will be the entity-specific name suffix
                entity_registry_enabled_default=False, # Keep this as per original logic
            )

            super().__init__(coordinator, appliance, entity_description)
            # The base class (HomeConnectEntity) will handle:
            # - Setting self.entity_description = entity_description
            # - Setting self._attr_unique_id = f"{appliance.info.ha_id}-{entity_description.key}"
            # - Inheriting _attr_has_entity_name = True
            # - Home Assistant will compose the full name as "Device Name" + "entity_description.name"

            # No need to manually set self._attr_name or self._attr_unique_id here if the base class handles it appropriately with the new entity_description.
            # If the unique_id f"{appliance.info.ha_id}-{desc}" (where desc is the human-readable string) is strictly required, 
            # then _attr_unique_id would still need to be set manually after super().__init__ call, 
            # but using program.key is generally preferred for unique_id stability.
    ```

By making these changes, `HomeConnectProgramSwitch` will adhere to the `has-entity-name` rule, allowing Home Assistant to manage its naming consistently with other entities. Given that this entity class is deprecated, the developers might choose to accept this minor inconsistency until its removal. However, for strict compliance, the change is recommended.

_Created at 2025-05-10 20:26:39. Prompt tokens: 139519, Output tokens: 1843, Total tokens: 147825_
