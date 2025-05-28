# overkiz: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule requires that common patterns like data update coordinators and base entities be placed in dedicated files, specifically `coordinator.py` for coordinators and `entity.py` for base entities. This rule applies to the `overkiz` integration as it utilizes both a data update coordinator and base entity classes.

The `overkiz` integration fully complies with this rule:

1.  **Coordinator:**
    *   The integration defines its data update coordinator, `OverkizDataUpdateCoordinator`, within the `homeassistant/components/overkiz/coordinator.py` file.
        ```python
        # homeassistant/components/overkiz/coordinator.py
        class OverkizDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Device]]):
            """Class to manage fetching data from Overkiz platform."""
            # ...
        ```
    *   This coordinator is then imported and used in `homeassistant/components/overkiz/__init__.py` for managing data updates.
        ```python
        # homeassistant/components/overkiz/__init__.py
        from .coordinator import OverkizDataUpdateCoordinator
        # ...
        coordinator = OverkizDataUpdateCoordinator(
            hass,
            entry,
            LOGGER,
            client=client,
            devices=setup.devices,
            places=setup.root_place,
        )
        ```

2.  **Base Entity:**
    *   The integration defines its base entity classes, `OverkizEntity` and `OverkizDescriptiveEntity`, within the `homeassistant/components/overkiz/entity.py` file.
        ```python
        # homeassistant/components/overkiz/entity.py
        class OverkizEntity(CoordinatorEntity[OverkizDataUpdateCoordinator]):
            """Representation of an Overkiz device entity."""
            # ...

        class OverkizDescriptiveEntity(OverkizEntity):
            """Representation of a Overkiz device entity based on a description."""
            # ...
        ```
    *   These base classes are then used by various platform entities. For example, in `homeassistant/components/overkiz/sensor.py`:
        ```python
        # homeassistant/components/overkiz/sensor.py
        from .entity import OverkizDescriptiveEntity, OverkizEntity
        # ...
        class OverkizStateSensor(OverkizDescriptiveEntity, SensorEntity):
            # ...
        class OverkizHomeKitSetupCodeSensor(OverkizEntity, SensorEntity):
            # ...
        ```
    *   And in `homeassistant/components/overkiz/light.py`:
        ```python
        # homeassistant/components/overkiz/light.py
        from .entity import OverkizEntity
        # ...
        class OverkizLight(OverkizEntity, LightEntity):
            # ...
        ```

The separation of the coordinator and base entity logic into their respective `coordinator.py` and `entity.py` files aligns with the requirements of the `common-modules` rule, promoting consistency and maintainability.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:09:03. Prompt tokens: 86914, Output tokens: 818, Total tokens: 88516_
