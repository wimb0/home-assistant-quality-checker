# adax: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule applies to the `adax` integration because it defines entities (specifically `ClimateEntity` instances). The rule requires entities to set `_attr_has_entity_name = True` to improve the consistency and contextual presentation of entity names in Home Assistant.

The `adax` integration currently does **not** follow this rule for its climate entities.

1.  **`AdaxDevice` (Cloud Connection):**
    Located in `homeassistant/components/adax/climate.py`.
    *   This class does not set `_attr_has_entity_name = True`.
    *   It currently sets `self._attr_name = self.room["name"]`.
    *   The `DeviceInfo`'s `name` attribute is set using `name=cast(str | None, self.name)`, which means the device name effectively becomes the same as the entity name (`self.room["name"]`).
    *   A comment in the code explicitly points out the need for this change:
        ```python
        # Instead of setting the device name to the entity name, adax
        # should be updated to set has_entity_name = True, and set the entity
        # name to None
        ```
        This indicates that `self.room["name"]` should be the device's name, and the entity (being the primary climate control for that device) should have `_attr_name = None` along with `_attr_has_entity_name = True`.

2.  **`LocalAdaxDevice` (Local Connection):**
    Located in `homeassistant/components/adax/climate.py`.
    *   This class does not set `_attr_has_entity_name = True`.
    *   `_attr_name` is not explicitly set in its `__init__` method, so it defaults to `None` (inherited from `Entity`). This part is fine if it's the primary entity.
    *   However, the `DeviceInfo`'s `name` attribute is not set:
        ```python
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="Adax",
            # name is missing here
        )
        ```
        For `_attr_has_entity_name = True` to work correctly when `_attr_name = None`, the `DeviceInfo` must have a `name` attribute, as this name will be used for the entity.

Due to these omissions, the integration does not comply with the `has-entity-name` rule.

## Suggestions

To make the `adax` integration compliant with the `has-entity-name` rule, the following changes are recommended in `homeassistant/components/adax/climate.py`:

1.  **For `AdaxDevice` class:**
    *   Add the `_attr_has_entity_name` attribute and set it to `True`.
    *   Set `_attr_name` to `None`, as the climate entity is the primary feature of the device.
    *   Ensure the `DeviceInfo` `name` attribute is explicitly set to `self.room["name"]`.

    **Current Code:**
    ```python
    class AdaxDevice(CoordinatorEntity[AdaxCloudCoordinator], ClimateEntity):
        # ...
        def __init__(
            self,
            coordinator: AdaxCloudCoordinator,
            device_id: str,
        ) -> None:
            # ...
            self._attr_name = self.room["name"]
            self._attr_unique_id = f"{self.room['homeId']}_{self._device_id}"
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device_id)},
                # Instead of setting the device name to the entity name, adax
                # should be updated to set has_entity_name = True, and set the entity
                # name to None
                name=cast(str | None, self.name),
                manufacturer="Adax",
            )
            # ...
    ```

    **Suggested Code:**
    ```python
    class AdaxDevice(CoordinatorEntity[AdaxCloudCoordinator], ClimateEntity):
        _attr_has_entity_name = True
        _attr_name = None  # Main entity for the device
        # ... (other class attributes like _attr_hvac_modes remain)

        def __init__(
            self,
            coordinator: AdaxCloudCoordinator,
            device_id: str,
        ) -> None:
            """Initialize the heater."""
            super().__init__(coordinator)
            self._adax_data_handler: Adax = coordinator.adax_data_handler
            self._device_id = device_id

            # _attr_name is now None (set at class level)
            self._attr_unique_id = f"{self.room['homeId']}_{self._device_id}"
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device_id)},
                name=self.room["name"],  # Set device name from room name
                manufacturer="Adax",
            )
            self._apply_data(self.room)
            # ...
    ```
    *Why these changes?*
    Setting `_attr_has_entity_name = True` enables the new naming behavior. Setting `_attr_name = None` indicates this is the main entity, so its name will be derived from the device name. `self.room["name"]` becomes the device name, which is appropriate.

2.  **For `LocalAdaxDevice` class:**
    *   Add the `_attr_has_entity_name` attribute and set it to `True`.
    *   Ensure `_attr_name` remains `None` (it defaults to `None` currently, which is correct for a primary entity).
    *   Set the `name` attribute in `DeviceInfo`. A good candidate for the device name would be the title of the config entry, which is the `unique_id` (MAC address) for local devices. Alternatively, a more user-friendly name like "Adax Heater" or "Adax Heater [last part of MAC]" could be used. Using the config entry title is a common pattern.

    **Current Code:**
    ```python
    class LocalAdaxDevice(CoordinatorEntity[AdaxLocalCoordinator], ClimateEntity):
        # ...
        def __init__(self, coordinator: AdaxLocalCoordinator, unique_id: str) -> None:
            """Initialize the heater."""
            super().__init__(coordinator)
            self._adax_data_handler: AdaxLocal = coordinator.adax_data_handler
            self._attr_unique_id = unique_id
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, unique_id)},
                manufacturer="Adax",
            )
            # _attr_name is implicitly None
            # ...
    ```

    **Suggested Code:**
    ```python
    class LocalAdaxDevice(CoordinatorEntity[AdaxLocalCoordinator], ClimateEntity):
        _attr_has_entity_name = True
        _attr_name = None  # Main entity for the device
        # ... (other class attributes like _attr_hvac_modes remain)

        def __init__(self, coordinator: AdaxLocalCoordinator, unique_id: str) -> None:
            """Initialize the heater."""
            super().__init__(coordinator)
            self._adax_data_handler: AdaxLocal = coordinator.adax_data_handler
            self._attr_unique_id = unique_id
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, unique_id)},
                name=coordinator.config_entry.title,  # Use config entry title as device name
                manufacturer="Adax",
            )
            # _attr_name is None (set at class level)
            # ...
    ```
    *Why these changes?*
    Setting `_attr_has_entity_name = True` enables the new naming behavior. `_attr_name` being `None` means the entity name will be the device name. Providing a `name` in `DeviceInfo` (e.g., from the config entry title, which is the MAC address/`unique_id` for local devices) ensures the device has a name that can be used for the entity.

By implementing these changes, the `adax` integration will correctly use the `has_entity_name` attribute, leading to more consistent and user-friendly entity naming within Home Assistant.

_Created at 2025-05-14 15:07:14. Prompt tokens: 6748, Output tokens: 2043, Total tokens: 12274_
