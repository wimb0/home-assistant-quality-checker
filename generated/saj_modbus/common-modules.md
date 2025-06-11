# saj_modbus: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **todo**                                                                 |

## Overview

The `common-modules` rule applies to this integration because it uses a `DataUpdateCoordinator` for data fetching and has multiple entity platforms (`sensor`, `number`) with shared logic that would benefit from a common base entity class.

The integration currently does **not** follow this rule for two reasons:

1.  **Coordinator Location:** The `DataUpdateCoordinator` implementation, `SAJModbusHub`, is defined in `hub.py`. The rule requires that coordinators be placed in a file named `coordinator.py` to improve consistency across integrations.
2.  **Missing Base Entity:** The `sensor` and `number` platforms define their own entity classes (`SajSensor` in `sensor.py` and `SajNumber` in `number.py`) which share significant boilerplate code. For instance, their `__init__` methods both handle the coordinator, device info, platform name, and entity description. A common base entity should be created in `entity.py` to abstract this shared logic, but this file and class do not exist.

## Suggestions

### 1. Relocate the Coordinator to `coordinator.py`

To align with Home Assistant's standard structure, the data update coordinator should be moved to its own file.

1.  **Create `coordinator.py`:**
    Create a new file: `homeassistant/components/saj_modbus/coordinator.py`.

2.  **Move and Rename the Class:**
    Move the `SAJModbusHub` class from `homeassistant/components/saj_modbus/hub.py` to the new `coordinator.py`. It is also best practice to rename the class to be more descriptive, for example, `SajModbusCoordinator`.

    ```python
    # In homeassistant/components/saj_modbus/coordinator.py
    # ... (imports)
    
    class SajModbusCoordinator(DataUpdateCoordinator[dict]):
        """Class to manage fetching SAJ Modbus data."""
        # ... (rest of the class code from SAJModbusHub)
    ```

3.  **Update Imports:**
    Update all files that were importing `SAJModbusHub` from `hub.py` to import `SajModbusCoordinator` from `coordinator.py` instead. This includes `__init__.py`, `sensor.py`, `number.py`, and `services.py`.

    For example, in `__init__.py`:
    ```python
    # from .hub import SAJModbusHub
    from .coordinator import SajModbusCoordinator
    
    # ...
    # hub = SAJModbusHub(hass, name, host, port, scan_interval)
    hub = SajModbusCoordinator(hass, name, host, port, scan_interval)
    ```

4.  **Delete `hub.py`:**
    Once the class is moved and all references are updated, the now-empty `hub.py` file can be deleted.

### 2. Create a Common Base Entity in `entity.py`

To reduce code duplication between the `sensor` and `number` entities, a shared base class should be created.

1.  **Create `entity.py`:**
    Create a new file: `homeassistant/components/saj_modbus/entity.py`.

2.  **Define the Base Entity:**
    Add a base class that encapsulates the common logic from `SajSensor` and `SajNumber`. This includes handling the coordinator, device info, and unique ID creation.

    ```python
    # In homeassistant/components/saj_modbus/entity.py
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
    
    from .coordinator import SajModbusCoordinator # Assumes step 1 is done
    
    class SajModbusEntity(CoordinatorEntity[SajModbusCoordinator]):
        """Defines a base entity for the SAJ Modbus integration."""
    
        def __init__(
            self,
            platform_name: str,
            coordinator: SajModbusCoordinator,
            device_info,
            description,
        ) -> None:
            """Initialize the SAJ Modbus entity."""
            super().__init__(coordinator)
            self._platform_name = platform_name
            self._attr_device_info = device_info
            self.entity_description = description
            self._attr_unique_id = f"{platform_name}_{description.key}"
    ```

3.  **Refactor Platform Entities:**
    Update `SajSensor` and `SajNumber` to inherit from this new base class. This will significantly simplify their `__init__` methods.

    **Example for `sensor.py`:**
    ```python
    # In homeassistant/components/saj_modbus/sensor.py
    # ...
    # from homeassistant.helpers.update_coordinator import CoordinatorEntity
    from homeassistant.components.sensor import SensorEntity
    from .entity import SajModbusEntity
    # ...
    
    class SajSensor(SajModbusEntity, SensorEntity):
        """Representation of an SAJ Modbus sensor."""

        # The __init__ is now inherited from SajModbusEntity and can be removed,
        # unless there is sensor-specific logic to add.
    
        @property
        def name(self):
            """Return the name."""
            # This logic is specific to the sensor, so it remains.
            return f"{self._platform_name} {self.entity_description.name}"

        # The unique_id property can be removed as _attr_unique_id is now set in the base class.
    
        @property
        def native_value(self):
            """Return the native value of the sensor."""
            return self.coordinator.data.get(self.entity_description.key, None)
    
    # ...
    ```

    **Example for `number.py`:**
    ```python
    # In homeassistant/components/saj_modbus/number.py
    # ...
    from homeassistant.components.number import NumberEntity
    # from homeassistant.helpers.update_coordinator import CoordinatorEntity
    from .entity import SajModbusEntity
    # ...
    
    class SajNumber(SajModbusEntity, NumberEntity):
        """Representation of an SAJ Modbus number."""
        _attr_has_entity_name = True
    
        # The __init__ is inherited from SajModbusEntity and can be removed.
    
        @property
        def available(self) -> bool:
            """Return entity availability."""
            return self.native_value is not None
    
        @property
        def native_value(self) -> float | None:
            """Return the state of the number entity."""
            return self.coordinator.data.get(self.entity_description.key, None)
    
        def set_native_value(self, value: float) -> None:
            """Update the current value."""
            self.coordinator.set_value(self.entity_description.key, value)
    ```

---

_Created at 2025-06-11 21:31:13. Prompt tokens: 16584, Output tokens: 1692, Total tokens: 21656._

_AI can be wrong. Always verify the report and the code against the rule._
