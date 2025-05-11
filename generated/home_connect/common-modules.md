# home_connect: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `common-modules` rule mandates that common patterns like data update coordinators and base entity classes should be placed in designated files, specifically `coordinator.py` for coordinators and `entity.py` for base entities. This rule applies to the `home_connect` integration as it utilizes both of these patterns.

The `home_connect` integration fully adheres to this rule.

1.  **Coordinator:**
    The integration defines its data update coordinator, `HomeConnectCoordinator`, within the `coordinator.py` file. This class inherits from `DataUpdateCoordinator`, as shown in the code:
    ```python
    # coordinator.py
    class HomeConnectCoordinator(
        DataUpdateCoordinator[dict[str, HomeConnectApplianceData]]
    ):
        """Class to manage fetching Home Connect data."""
        # ...
    ```
    This centralizes the data fetching logic as recommended.

2.  **Base Entity:**
    The integration defines a base entity class, `HomeConnectEntity`, within the `entity.py` file. This class inherits from `CoordinatorEntity` and serves as the foundation for various specific entity types within the integration.
    ```python
    # entity.py
    class HomeConnectEntity(CoordinatorEntity[HomeConnectCoordinator]):
        """Generic Home Connect entity (base class)."""
        # ...
    ```
    Additionally, `HomeConnectOptionEntity` is also defined in `entity.py` and inherits from `HomeConnectEntity`:
    ```python
    # entity.py
    class HomeConnectOptionEntity(HomeConnectEntity):
        """Class for entities that represents program options."""
        # ...
    ```
    Other entity platform files (e.g., `sensor.py`, `switch.py`, `light.py`) correctly import and use `HomeConnectEntity` as their base class. For instance, in `sensor.py`:
    ```python
    # sensor.py
    from .entity import HomeConnectEntity
    # ...
    class HomeConnectSensor(HomeConnectEntity, SensorEntity):
        """Sensor class for Home Connect."""
        # ...
    ```
    This structure promotes code reuse and consistency across different entity platforms.

The `home_connect` integration correctly places its coordinator in `coordinator.py` and its base entity class(es) in `entity.py`, thus satisfying the `common-modules` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 20:17:45. Prompt tokens: 138864, Output tokens: 636, Total tokens: 140335_
