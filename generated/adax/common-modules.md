# adax: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **todo**                                                                 |

## Overview

The `common-modules` rule requires that common patterns, such as data update coordinators and base entities, are placed in designated files (`coordinator.py` and `entity.py`, respectively) to enhance consistency and developer experience.

This rule applies to the `adax` integration because:
1.  It utilizes `DataUpdateCoordinator` for managing data fetching for both cloud and local connections.
2.  It defines multiple climate entity classes (`AdaxDevice` for cloud and `LocalAdaxDevice` for local) that share a significant number of attributes and functionalities, making a base entity class beneficial for code deduplication.

The `adax` integration partially follows this rule:
*   **Coordinators:** The integration correctly places its coordinator classes (`AdaxCloudCoordinator` and `AdaxLocalCoordinator`) in `homeassistant/components/adax/coordinator.py`. This part of the rule is satisfied.
*   **Base Entity:** The integration does NOT use a common base entity class in a `entity.py` file. The two climate entity classes, `AdaxDevice` and `LocalAdaxDevice` defined in `homeassistant/components/adax/climate.py`, have several duplicated class attributes.

Specifically, the following attributes are duplicated or highly similar across `AdaxDevice` and `LocalAdaxDevice`:
*   `_attr_hvac_modes`
*   `_attr_max_temp`
*   `_attr_min_temp`
*   `_attr_supported_features`
*   `_attr_target_temperature_step`
*   `_attr_temperature_unit`
*   The `manufacturer` in `_attr_device_info` is consistently "Adax".

The absence of a base entity in `entity.py` to consolidate these common characteristics means the integration does not fully adhere to the `common-modules` rule regarding base entities.

## Suggestions

To make the `adax` integration compliant with the `common-modules` rule, the following changes are recommended:

1.  **Create `entity.py`:**
    Add a new file `homeassistant/components/adax/entity.py`.

2.  **Define a Base Entity Class:**
    In the new `entity.py`, define a base class for Adax climate entities. This class should inherit from `CoordinatorEntity` and `ClimateEntity` and include the common attributes.

    ```python
    # homeassistant/components/adax/entity.py
    from typing import TypeVar

    from homeassistant.components.climate import (
        ClimateEntity,
        ClimateEntityFeature,
        HVACMode,
    )
    from homeassistant.const import (
        PRECISION_WHOLE,
        UnitOfTemperature,
    )
    from homeassistant.helpers.device_registry import DeviceInfo
    from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

    from .const import DOMAIN

    _CoordinatorT = TypeVar("_CoordinatorT", bound=DataUpdateCoordinator) # type: ignore[type-arg]


    class AdaxBaseClimateEntity(CoordinatorEntity[_CoordinatorT], ClimateEntity):
        """Base class for Adax climate entities."""

        _attr_has_entity_name = True  # Recommended for consistency
        _attr_temperature_unit = UnitOfTemperature.CELSIUS
        _attr_target_temperature_step = PRECISION_WHOLE
        _attr_min_temp = 5
        _attr_max_temp = 35
        _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        _attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )

        def __init__(
            self,
            coordinator: _CoordinatorT,
            unique_id_suffix: str, # Or the full unique_id if consistently formed
            device_name: str
        ) -> None:
            """Initialize the Adax base climate entity."""
            super().__init__(coordinator)
            # Note: unique_id construction might need coordinator data not available yet.
            # Consider setting unique_id and device_info in derived classes if complex.
            # For this example, we assume unique_id_suffix and device_name are passed.
            self._attr_unique_id = unique_id_suffix # This might need to be the full unique_id
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, self.unique_id)}, # self.unique_id refers to _attr_unique_id
                name=device_name,
                manufacturer="Adax",
                # model and sw_version could be added if available from coordinator
            )
            # If _attr_has_entity_name = True, self._attr_name should be None (default for ClimateEntity)
    ```

3.  **Refactor Climate Entities:**
    Modify `AdaxDevice` and `LocalAdaxDevice` in `homeassistant/components/adax/climate.py` to inherit from `AdaxBaseClimateEntity` and remove the duplicated attributes.

    Example for `AdaxDevice`:
    ```python
    # homeassistant/components/adax/climate.py
    # ... other imports
    from .entity import AdaxBaseClimateEntity
    from .coordinator import AdaxCloudCoordinator # Keep this for type hinting

    class AdaxDevice(AdaxBaseClimateEntity[AdaxCloudCoordinator]):
        """Representation of an Adax cloud-connected heater."""

        def __init__(
            self,
            coordinator: AdaxCloudCoordinator,
            device_id: str,
        ) -> None:
            """Initialize the heater."""
            # Determine unique_id and device_name for the base class
            # This might require accessing coordinator.data, ensure it's populated.
            # The original AdaxDevice sets unique_id and name after super().__init__(coordinator)
            # which is fine. The base class can define attributes, and __init__ can be tailored.

            # Option 1: Base class only defines attributes, __init__ sets them up.
            super().__init__(coordinator) # Call CoordinatorEntity's __init__
            self._adax_data_handler: Adax = coordinator.adax_data_handler
            self._device_id = device_id

            # Set unique_id and device_info here, potentially using common manufacturer from base if not fully handled by base __init__
            room_data = self.coordinator.data[self._device_id]
            self._attr_unique_id = f"{room_data['homeId']}_{self._device_id}"
            # If AdaxBaseClimateEntity._attr_has_entity_name = True, self._attr_name should be None
            # The device name goes into DeviceInfo
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, self.unique_id)},
                name=room_data["name"], # This becomes the device name
                manufacturer="Adax", # Or inherit from base
            )
            # Remove duplicated _attr_* class variables as they are now in AdaxBaseClimateEntity
            self._apply_data(room_data)

        # ... other AdaxDevice specific methods and properties (like `room` property)
        # Ensure _apply_data and other methods correctly interact with attributes.
    ```
    A similar refactoring would apply to `LocalAdaxDevice`. The key is that the common class attributes (`_attr_hvac_modes`, `_attr_max_temp`, etc.) are inherited from `AdaxBaseClimateEntity` and removed from the derived classes. The `__init__` method of the derived classes would call `super().__init__(coordinator, ...)` if the base class `__init__` is designed to set up `unique_id` and `device_info`, or call `super().__init__(coordinator)` and then set these attributes themselves.

**Why these changes satisfy the rule:**
*   Introducing `entity.py` with a `AdaxBaseClimateEntity` centralizes common entity code.
*   It reduces code duplication in `climate.py`, making the individual entity classes cleaner and more focused on their specific logic.
*   This aligns with the rule's goal of increasing consistency and maintainability by following established patterns for structuring integration code.
*   The comment within `AdaxDevice` (`# Instead of setting the device name to the entity name, adax should be updated to set has_entity_name = True...`) aligns with the suggestion to use `_attr_has_entity_name = True` in the base entity.

_Created at 2025-05-14 15:03:57. Prompt tokens: 6574, Output tokens: 2033, Total tokens: 15049_
