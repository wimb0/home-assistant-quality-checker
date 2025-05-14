# stiebel_eltron: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule requires entities to use the `_attr_has_entity_name = True` attribute along with `_attr_name` and `_attr_device_info` to standardize entity naming. This allows Home Assistant to consistently display entity names, often by combining the device name with a specific entity name (e.g., "My Device Temperature") or using the device name directly for the main entity of a device (when `_attr_name` is `None`).

This rule **applies** to the `stiebel_eltron` integration because it defines a `ClimateEntity`.

The `stiebel_eltron` integration currently does **not** follow this rule.
The `StiebelEltron` class in `climate.py` (the only entity class in this integration) does not implement the `has_entity_name` pattern:

1.  **`_attr_has_entity_name` is not set**: The class `StiebelEltron` does not set `_attr_has_entity_name = True`.
    ```python
    # homeassistant/components/stiebel_eltron/climate.py
    class StiebelEltron(ClimateEntity):
        # _attr_has_entity_name = True is missing
        _attr_hvac_modes = SUPPORT_HVAC
        # ...
    ```

2.  **`_attr_name` is not used**: The entity name is not controlled via `_attr_name`. Instead, an explicit `_name` instance variable is set in the constructor, and a `name` property directly returns this value.
    ```python
    # homeassistant/components/stiebel_eltron/climate.py
    def __init__(self, name: str, client: StiebelEltronAPI) -> None:
        """Initialize the unit."""
        self._name = name # Old pattern for entity naming
        # ...

    @property
    def name(self) -> str:
        """Return the name of the climate device."""
        return self._name
    ```
    The `has-entity-name` pattern expects `_attr_name` to be set (e.g., to `None` for the main entity of a device, or a string like "Temperature" for specific aspects).

3.  **`_attr_device_info` is not set**: The `StiebelEltron` entity does not define `_attr_device_info`. The `has_entity_name` mechanism relies on `DeviceInfo` to get the device name, which is then combined with `_attr_name` (or used alone if `_attr_name` is `None`).
    The entity is initialized with `entry.title` as its name:
    ```python
    # homeassistant/components/stiebel_eltron/climate.py
    async def async_setup_entry(
        # ...
    ) -> None:
        # ...
        async_add_entities([StiebelEltron(entry.title, entry.runtime_data)], True)
    ```
    While this results in a reasonable entity name, it doesn't use the standardized `has_entity_name` mechanism which ties into the device registry for better name generation and context.

Because these attributes and patterns are not used, the integration does not conform to the `has-entity-name` rule.

## Suggestions

To make the `stiebel_eltron` integration compliant with the `has-entity-name` rule, the following changes should be made to the `StiebelEltron` class in `homeassistant/components/stiebel_eltron/climate.py`:

1.  **Set `_attr_has_entity_name` to `True`**:
    Add `_attr_has_entity_name = True` as a class attribute.

2.  **Set `_attr_name` to `None`**:
    Since the climate entity is the primary (and only) entity for the Stiebel Eltron device, its name should ideally be the device name. This is achieved by setting `_attr_name = None`. Add this as a class attribute.

3.  **Define `_attr_device_info`**:
    The entity needs to be associated with a device. This is done by setting `_attr_device_info`. The device name should come from the `ConfigEntry`'s title.
    Modify the `__init__` method to accept the `ConfigEntry` object to access its properties like `entry_id` and `title`. Also, set `_attr_unique_id` for the entity.

4.  **Remove the custom `name` property and `self._name`**:
    With `_attr_has_entity_name = True` and `_attr_name = None`, the base `Entity` class will handle the naming. The custom `name` property and the `self._name` instance variable are no longer needed.

5.  **Update `async_setup_entry` in `climate.py`**:
    Pass the full `ConfigEntry` object to the `StiebelEltron` constructor instead of just `entry.title`.

**Example Code Changes:**

In `homeassistant/components/stiebel_eltron/climate.py`:

```python
from __future__ import annotations

import logging
from typing import Any

from pystiebeleltron.pystiebeleltron import StiebelEltronAPI

from homeassistant.components.climate import (
    PRESET_ECO,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
# Import DeviceInfo and StiebelEltronConfigEntry if not already properly imported for type hinting
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import StiebelEltronConfigEntry # Ensure this import provides the correct type
from .const import DOMAIN # Import DOMAIN from your .const file

# ... (rest of the imports and constants)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: StiebelEltronConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up STIEBEL ELTRON climate platform."""
    client = entry.runtime_data
    # Pass the full entry object to the entity constructor
    async_add_entities([StiebelEltron(entry, client)], True)


class StiebelEltron(ClimateEntity):
    """Representation of a STIEBEL ELTRON heat pump."""

    _attr_has_entity_name = True
    _attr_name = None  # Main entity, name will be taken from device name

    _attr_hvac_modes = SUPPORT_HVAC
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, entry: StiebelEltronConfigEntry, client: StiebelEltronAPI) -> None:
        """Initialize the unit."""
        # self._name = name  # Remove this line
        self._client = client
        
        # Set unique ID for the entity
        self._attr_unique_id = entry.entry_id 
        
        # Set device information
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,  # Device name comes from the config entry title
            manufacturer="STIEBEL ELTRON",
            # model=client.get_some_model_identifier(), # If available
            # sw_version=client.get_firmware_version(), # If available
        )
        
        # Initialize other attributes if needed, but not _name
        self._target_temperature: float | int | None = None
        self._current_temperature: float | int | None = None
        self._current_humidity: float | int | None = None
        self._operation: str | None = None
        self._filter_alarm: bool | None = None

    def update(self) -> None:
        """Update unit attributes."""
        self._client.update()

        self._target_temperature = self._client.get_target_temp()
        self._current_temperature = self._client.get_current_temp()
        self._current_humidity = self._client.get_current_humidity()
        self._filter_alarm = self._client.get_filter_alarm_status()
        self._operation = self._client.get_operation()

        _LOGGER.debug(
            "Update %s, current temp: %s", self.name, self._current_temperature # Use self.name (from base class)
        )

    @property
    def extra_state_attributes(self) -> dict[str, bool | None]:
        """Return device specific state attributes."""
        return {"filter_alarm": self._filter_alarm}

    # Remove the name property, as it's handled by the base class
    # @property
    # def name(self) -> str:
    #     """Return the name of the climate device."""
    #     return self._name

    # ... (rest of the properties and methods remain the same)
```

**Why these changes satisfy the rule:**

*   Setting `_attr_has_entity_name = True` signals to Home Assistant that the entity uses the new naming system.
*   Setting `_attr_name = None` indicates that this entity is the main feature of the device, and its name should be the device's name.
*   Defining `_attr_device_info` links the entity to a device in the Home Assistant device registry. The `name` field in `DeviceInfo` (e.g., `entry.title`) provides the "Device Name" part for the entity naming logic.
*   Removing the explicit `name` property allows the base `Entity` class to correctly construct the entity's name based on `_attr_has_entity_name`, `_attr_name`, and the device name from `_attr_device_info`.

These changes will ensure that the `stiebel_eltron` integration adheres to the recommended entity naming conventions, improving consistency within Home Assistant.

_Created at 2025-05-14 14:58:16. Prompt tokens: 6200, Output tokens: 2470, Total tokens: 13583_
