# wled: entity-category

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [entity-category](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-category)                                                     |
| Status | **todo**                                       |
| Reason |  |

## Overview

The `entity-category` rule requires that entities are assigned an appropriate `EntityCategory` (e.g., `CONFIG` or `DIAGNOSTIC`) when the default category (`None`, implying a primary control or sensor) is inappropriate. This ensures correct classification and identification of entities, particularly for auto-generated dashboards and system organization.

The `wled` integration defines several entity types across different platforms: `button`, `light`, `number`, `select`, `sensor`, `switch`, and `update`.

Most entities in the `wled` integration correctly apply entity categories or appropriately use the default category:

*   **Sensor Entities (`sensor.py`):** All sensor entities (e.g., `estimated_current`, `uptime`, `wifi_signal`, `ip`) are correctly assigned `EntityCategory.DIAGNOSTIC` via their `WLEDSensorEntityDescription`. This is appropriate as they provide diagnostic information about the WLED device.
*   **Button Entities (`button.py`):**
    *   `WLEDRestartButton`: Correctly assigned `_attr_entity_category = EntityCategory.CONFIG`. Restarting is a configuration/management action.
*   **Number Entities (`number.py`):**
    *   `WLEDNumber` entities for "speed" and "intensity": Correctly assigned `entity_category=EntityCategory.CONFIG` via `WLEDNumberEntityDescription`. These control configuration aspects of effects.
*   **Switch Entities (`switch.py`):**
    *   `WLEDNightlightSwitch`, `WLEDSyncSendSwitch`, `WLEDSyncReceiveSwitch`, `WLEDReverseSwitch`: All correctly assigned `_attr_entity_category = EntityCategory.CONFIG`. These control various configuration settings or modes of the WLED device.
*   **Select Entities (`select.py`):**
    *   `WLEDLiveOverrideSelect`: Correctly assigned `_attr_entity_category = EntityCategory.CONFIG`. This controls a configuration setting.
    *   `WLEDPaletteSelect`: Correctly assigned `_attr_entity_category = EntityCategory.CONFIG`. Selecting a palette is a configuration aspect of an effect.
    *   `WLEDPresetSelect` and `WLEDPlaylistSelect`: Do not have an explicit `entity_category` set, thus defaulting to `None`. This is appropriate as selecting a preset or playlist is a primary control action for the WLED device.
*   **Light Entities (`light.py`):**
    *   `WLEDMainLight` and `WLEDSegmentLight`: Do not have an explicit `entity_category` set, defaulting to `None`. This is appropriate as lights are primary control entities.

However, one entity type does not have an explicit `EntityCategory` assigned where it would be appropriate:

*   **Update Entity (`update.py`):**
    *   The `WLEDUpdateEntity` class does not set an `_attr_entity_category`. Update entities typically represent firmware or software updates and are generally considered configuration or diagnostic. The default category (`None`) is inappropriate as an update entity is not a primary control or sensor for the device's main function (lighting). It should be categorized, commonly as `EntityCategory.CONFIG`.

    ```python
    # update.py
    class WLEDUpdateEntity(WLEDEntity, UpdateEntity):
        """Defines a WLED update entity."""

        _attr_device_class = UpdateDeviceClass.FIRMWARE
        _attr_supported_features = (
            UpdateEntityFeature.INSTALL | UpdateEntityFeature.SPECIFIC_VERSION
        )
        _attr_title = "WLED"
        # Missing: _attr_entity_category = EntityCategory.CONFIG

        def __init__(
            self,
            coordinator: WLEDDataUpdateCoordinator,
            releases_coordinator: WLEDReleasesDataUpdateCoordinator,
        ) -> None:
            # ...
    ```

Because the `WLEDUpdateEntity` does not have an appropriate `EntityCategory` assigned, the integration does not fully follow the `entity-category` rule.

## Suggestions

To make the `wled` integration compliant with the `entity-category` rule, the `WLEDUpdateEntity` should be assigned an appropriate entity category. `EntityCategory.CONFIG` is suitable for update entities as they relate to the configuration and management of the device's firmware.

1.  **Modify `update.py`:**
    Add `_attr_entity_category = EntityCategory.CONFIG` to the `WLEDUpdateEntity` class.
    Ensure `EntityCategory` is imported from `homeassistant.const`.

    **Example (`update.py`):**
    ```python
    from __future__ import annotations

    from typing import Any, cast

    from homeassistant.components.update import (
        UpdateDeviceClass,
        UpdateEntity,
        UpdateEntityFeature,
    )
    from homeassistant.const import EntityCategory  # Add this import
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from . import WLED_KEY, WLEDConfigEntry
    from .coordinator import WLEDDataUpdateCoordinator, WLEDReleasesDataUpdateCoordinator
    from .entity import WLEDEntity
    from .helpers import wled_exception_handler


    async def async_setup_entry(
        hass: HomeAssistant,
        entry: WLEDConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up WLED update based on a config entry."""
        async_add_entities([WLEDUpdateEntity(entry.runtime_data, hass.data[WLED_KEY])])


    class WLEDUpdateEntity(WLEDEntity, UpdateEntity):
        """Defines a WLED update entity."""

        _attr_device_class = UpdateDeviceClass.FIRMWARE
        _attr_supported_features = (
            UpdateEntityFeature.INSTALL | UpdateEntityFeature.SPECIFIC_VERSION
        )
        _attr_title = "WLED"
        _attr_entity_category = EntityCategory.CONFIG  # Add this line

        def __init__(
            self,
            coordinator: WLEDDataUpdateCoordinator,
            releases_coordinator: WLEDReleasesDataUpdateCoordinator,
        ) -> None:
            """Initialize the update entity."""
            super().__init__(coordinator=coordinator)
            self.releases_coordinator = releases_coordinator
            self._attr_unique_id = coordinator.data.info.mac_address

        # ... rest of the class
    ```

By assigning `EntityCategory.CONFIG` to `WLEDUpdateEntity`, it will be correctly classified as a configuration-related entity, aligning with Home Assistant best practices and the requirements of the `entity-category` rule.

_Created at 2025-05-10 23:00:10. Prompt tokens: 20214, Output tokens: 1614, Total tokens: 23846_
