# home_connect: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unique-id` rule requires all entities created by an integration to have a unique ID. This allows Home Assistant to track entities across restarts and enables users to customize them (e.g., rename, change unit of measurement).

The `home_connect` integration defines a base entity class, `HomeConnectEntity` in `entity.py`. This base class consistently sets the `_attr_unique_id` for its instances in its `__init__` method:
```python
# entity.py
class HomeConnectEntity(CoordinatorEntity[HomeConnectCoordinator]):
    # ...
    def __init__(
        self,
        coordinator: HomeConnectCoordinator,
        appliance: HomeConnectApplianceData,
        desc: EntityDescription,
        context_override: Any | None = None,
    ) -> None:
        # ...
        super().__init__(coordinator, context)
        # ...
        self._attr_unique_id = f"{appliance.info.ha_id}-{desc.key}"
        # ...
```
This pattern combines the appliance's unique hardware identifier (`appliance.info.ha_id`) with a key from the `EntityDescription` (`desc.key`) specific to the entity's function (e.g., a `SettingKey`, `StatusKey`, `EventKey`, or `OptionKey`). This ensures that the generated unique ID is unique across all entities for a given appliance and unique globally when combined with the integration domain and platform.

All specific entity types across the various platforms (`binary_sensor.py`, `button.py`, `light.py`, `number.py`, `select.py`, `sensor.py`, `switch.py`, `time.py`) inherit from `HomeConnectEntity` or its derivative `HomeConnectOptionEntity` (which itself inherits from `HomeConnectEntity` and thus the unique ID logic).

For example, in `sensor.py`:
```python
# sensor.py
class HomeConnectSensor(HomeConnectEntity, SensorEntity):
    """Sensor class for Home Connect."""
    # __init__ calls super().__init__(coordinator, appliance, description)
    # which uses the base class's unique_id logic.
    # ...
```
And in `light.py`:
```python
# light.py
class HomeConnectLight(HomeConnectEntity, LightEntity):
    """Light for Home Connect."""
    # __init__ calls super().__init__(coordinator, appliance, desc)
    # ...
```
This pattern is consistently followed.

A special case is `HomeConnectProgramSwitch` in `switch.py`:
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
        """Initialize the entity."""
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
                key=EventKey.BSH_COMMON_ROOT_ACTIVE_PROGRAM, # This key is not directly used for the unique_id
                entity_registry_enabled_default=False,
            ),
        )
        self._attr_name = f"{appliance.info.name} {desc}"
        self._attr_unique_id = f"{appliance.info.ha_id}-{desc}" # Explicitly sets unique_id
        self._attr_has_entity_name = False
```
Here, `_attr_unique_id` is explicitly set using a constructed string `desc` derived from the program key. This also ensures uniqueness as `appliance.info.ha_id` is unique per appliance, and the `desc` string (e.g., "Program HotAir" for an oven program) is unique per program type for that appliance.

Since all entities either use the base class's robust unique ID generation mechanism or implement a similarly robust one, the integration fully complies with the `entity-unique-id` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 20:23:53. Prompt tokens: 138775, Output tokens: 1099, Total tokens: 142246_
