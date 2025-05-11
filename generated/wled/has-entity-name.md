# wled: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule requires that all entities within an integration set the `_attr_has_entity_name = True` attribute. This promotes consistent entity naming, where the entity's full name is typically a combination of the device name and the entity-specific name (e.g., "Device Name Sensor Temperature"). If an entity represents the main feature of a device, its `_attr_name` can be set to `None`, resulting in the entity being named solely after the device.

This rule applies to the `wled` integration as it creates multiple entities.

The `wled` integration correctly follows this rule:

1.  **Base Entity Implementation**: The `WLEDEntity` class, located in `entity.py`, serves as the base class for all WLED entities. It correctly sets `_attr_has_entity_name = True` at the class level:
    ```python
    # entity.py
    class WLEDEntity(CoordinatorEntity[WLEDDataUpdateCoordinator]):
        """Defines a base WLED entity."""

        _attr_has_entity_name = True
        # ...
    ```
    All specific entity classes in the integration (e.g., `WLEDMainLight`, `WLEDSensorEntity`, `WLEDSwitch`, etc.) inherit from `WLEDEntity`, thereby inheriting `_attr_has_entity_name = True`.

2.  **Entity-Specific Naming**:
    *   Most entities use `_attr_translation_key` or `entity_description.translation_key` to define their specific name part, which is then combined with the device name by Home Assistant. For example, in `sensor.py`:
        ```python
        # sensor.py
        SENSORS: tuple[WLEDSensorEntityDescription, ...] = (
            WLEDSensorEntityDescription(
                key="estimated_current",
                translation_key="estimated_current",
                # ...
            ),
            # ...
        )

        class WLEDSensorEntity(WLEDEntity, SensorEntity):
            # ...
            def __init__(
                self,
                coordinator: WLEDDataUpdateCoordinator,
                description: WLEDSensorEntityDescription,
            ) -> None:
                super().__init__(coordinator=coordinator)
                self.entity_description = description
                # ...
        ```
        This results in names like "WLED Device Name Estimated current".

    *   For entities representing the main feature or a default representation, `_attr_name` is appropriately set to `None`. An example is `WLEDSegmentLight` for segment 0 in `light.py`:
        ```python
        # light.py
        class WLEDSegmentLight(WLEDEntity, LightEntity):
            # ...
            def __init__(
                self,
                coordinator: WLEDDataUpdateCoordinator,
                segment: int,
            ) -> None:
                # ...
                if segment == 0:
                    self._attr_name = None
                else:
                    self._attr_translation_placeholders = {"segment": str(segment)}
                # ...
        ```
        When `segment == 0` and `_attr_name = None`, the entity will be named after the WLED device itself (e.g., "WLED Device Name"), which is appropriate for the primary light control of a single-segment device.

    *   The `WLEDUpdateEntity` in `update.py` uses `_attr_title = "WLED"`. For `UpdateEntity`, `_attr_title` serves a similar purpose to `_attr_name` when `_attr_has_entity_name` is true, defining the entity-specific part of the name.
        ```python
        # update.py
        class WLEDUpdateEntity(WLEDEntity, UpdateEntity):
            _attr_title = "WLED"
            # ...
        ```
        This will result in an entity named "Device Name WLED".

    *   The `WLEDRestartButton` in `button.py` uses `_attr_device_class = ButtonDeviceClass.RESTART`. When `_attr_has_entity_name` is true and `_attr_name` is not explicitly set, entities often derive their name from the `device_class`. This is an accepted pattern.
        ```python
        # button.py
        class WLEDRestartButton(WLEDEntity, ButtonEntity):
            _attr_device_class = ButtonDeviceClass.RESTART
            # ...
        ```
        This will result in an entity named "Device Name Restart".

The integration consistently applies `_attr_has_entity_name = True` through its base entity and correctly manages the entity-specific name component using standard Home Assistant mechanisms (translation keys, `_attr_name = None`, `_attr_title`, or `device_class` inference).

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:28:24. Prompt tokens: 21662, Output tokens: 1219, Total tokens: 26629_
