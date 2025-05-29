# evohome: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **todo**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `has-entity-name` rule requires entities to set the `_attr_has_entity_name = True` attribute. This allows Home Assistant to generate more consistent and context-aware entity names, typically by combining the device name with the entity's specific name (if provided) or using the device name directly if the entity represents the main feature of the device.

This rule applies to the `evohome` integration as it creates `climate` and `water_heater` entities.

The `evohome` integration currently does **not** follow this rule. None of its entity classes (`EvoController`, `EvoZone` in `climate.py`, and `EvoDHW` in `water_heater.py`) set `_attr_has_entity_name = True`.

For example, in `homeassistant/components/evohome/climate.py`:
- The `EvoZone` class defines a `name` property but does not set `_attr_has_entity_name = True`.
- The `EvoController` class sets `self._attr_name` in its `__init__` method but also does not set `_attr_has_entity_name = True`.

Similarly, in `homeassistant/components/evohome/water_heater.py`:
- The `EvoDHW` class sets `self._attr_name` but does not set `_attr_has_entity_name = True`.

The absence of `_attr_has_entity_name = True` means the integration is not leveraging Home Assistant's modern entity naming conventions, which can lead to less consistent naming across the system.

## Suggestions

To make the `evohome` integration compliant with the `has-entity-name` rule, the following changes are recommended:

1.  **Set up DeviceInfo in the base entity class:**
    It's good practice for all entities belonging to a single physical device (the Evohome Total Connect Comfort system, TCS) to share common device information. This can be done in the `EvoEntity` base class.

    In `homeassistant/components/evohome/entity.py`, modify `EvoEntity.__init__`:
    ```python
    from homeassistant.helpers.device_registry import DeviceInfo # Add this import

    # ... inside EvoEntity __init__ method:
    def __init__(
        self,
        coordinator: EvoDataUpdateCoordinator,
        evo_device: evo.ControlSystem | evo.HotWater | evo.Zone,
    ) -> None:
        """Initialize an evohome-compatible entity (TCS, DHW, zone)."""
        super().__init__(coordinator, context=evo_device.id)
        self._evo_device = evo_device

        # Add common DeviceInfo for all entities related to this TCS
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.tcs.id)},
            name=coordinator.tcs.location.name, # This will be the "Device Name"
            manufacturer="HoneywellHome", # Or "Resideo" - check product branding
            model=coordinator.tcs.model,
        )

        self._device_state_attrs: dict[str, Any] = {}
    ```

2.  **Update `EvoController` entity (Climate):**
    This entity represents the main controller/system. Its name should be the device name.

    In `homeassistant/components/evohome/climate.py`, modify the `EvoController` class:
    ```python
    class EvoController(EvoClimateEntity):
        # ...
        _attr_has_entity_name = True  # Add this
        _attr_name = None  # Main entity for the device, name comes from DeviceInfo
        _attr_icon = "mdi:thermostat"
        # ...

        def __init__(
            self, coordinator: EvoDataUpdateCoordinator, evo_device: evo.ControlSystem
        ) -> None:
            """Initialize an evohome-compatible controller."""
            # No longer call super for EvoClimateEntity, call EvoEntity directly
            # if EvoClimateEntity doesn't do much in its __init__ beyond EvoEntity
            # Or ensure EvoClimateEntity also sets _attr_has_entity_name

            # EvoEntity's __init__ (which is super().__init__ for EvoClimateEntity)
            # will set _attr_device_info.
            # The _attr_name = None at class level is sufficient.
            # Remove: self._attr_name = evo_device.location.name
            super().__init__(coordinator, evo_device) # Ensure this calls EvoEntity.__init__ properly
            self._evo_id = evo_device.id
            self._attr_unique_id = evo_device.id
            # self._attr_name = evo_device.location.name # REMOVE THIS LINE

            self._evo_modes = [m[SZ_SYSTEM_MODE] for m in evo_device.allowed_system_modes]
            # ... rest of __init__
    ```
    *Why this change?* With `_attr_has_entity_name = True` and `_attr_name = None`, the entity's display name will be derived from `DeviceInfo.name` (e.g., "Home").

3.  **Update `EvoZone` entity (Climate):**
    These entities represent individual heating zones, which are features of the main Evohome system.

    In `homeassistant/components/evohome/climate.py`, modify the `EvoZone` class:
    ```python
    class EvoZone(EvoChild, EvoClimateEntity):
        _attr_has_entity_name = True # Add this
        # _attr_preset_modes = list(HA_PRESET_TO_EVO) # Keep this

        # _evo_device: evo.Zone # Keep this
        # _evo_id_attr = "zone_id" # Keep this
        # _evo_state_attr_names = (SZ_SETPOINT_STATUS, SZ_TEMPERATURE_STATUS) # Keep this

        def __init__(
            self, coordinator: EvoDataUpdateCoordinator, evo_device: evo.Zone
        ) -> None:
            """Initialize an evohome-compatible heating zone."""
            super().__init__(coordinator, evo_device)
            self._evo_id = evo_device.id

            # Set _attr_name to the zone's specific name
            self._attr_name = evo_device.name

            if evo_device.id == evo_device.tcs.id:
                self._attr_unique_id = f"{evo_device.id}z"
            else:
                self._attr_unique_id = evo_device.id
            # ... rest of __init__

        # Remove the name property if _attr_name is set in __init__
        # @property
        # def name(self) -> str | None:
        #     """Return the name of the evohome entity."""
        #     return self._evo_device.name # This logic is now in self._attr_name
    ```
    *Why this change?* With `_attr_has_entity_name = True` and `_attr_name` set to the zone's name (e.g., "Living Room"), the entity's display name will be "Device Name Living Room" (e.g., "Home Living Room").

4.  **Update `EvoDHW` entity (Water Heater):**
    This entity represents the Domestic Hot Water controller, another feature of the main system.

    In `homeassistant/components/evohome/water_heater.py`, modify the `EvoDHW` class:
    ```python
    class EvoDHW(EvoChild, WaterHeaterEntity):
        _attr_has_entity_name = True # Add this
        # _attr_name = "DHW controller" # This will be overridden in __init__
        _attr_icon = "mdi:thermometer-lines"
        # ...

        def __init__(
            self, coordinator: EvoDataUpdateCoordinator, evo_device: evo.HotWater
        ) -> None:
            """Initialize an evohome-compatible DHW controller."""
            super().__init__(coordinator, evo_device)
            self._evo_id = evo_device.id

            self._attr_unique_id = evo_device.id
            # Set _attr_name to the DHW's specific name
            self._attr_name = evo_device.name # This line is already present and correct

            # ... rest of __init__
    ```
    *Why this change?* Similar to zones, with `_attr_has_entity_name = True` and `_attr_name` set to the DHW unit's name (e.g., "DHW Controller"), the entity's display name will be "Device Name DHW Controller" (e.g., "Home DHW Controller").

By implementing these changes, the `evohome` integration will correctly use `_attr_has_entity_name`, aligning with Home Assistant's entity naming best practices and satisfying the rule. This will result in more predictable and user-friendly entity names. Remember to also import `DeviceInfo` from `homeassistant.helpers.device_registry` in `entity.py`.

---

_Created at 2025-05-29 11:45:45. Prompt tokens: 21918, Output tokens: 2229, Total tokens: 31145._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
