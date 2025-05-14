# stiebel_eltron: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `entity-unique-id` rule requires that all entities created by an integration have a unique ID. This ID is used by Home Assistant to track entities across restarts, allowing users to customize them (e.g., rename, change entity options).

This rule applies to the `stiebel_eltron` integration because it creates a `climate` entity.

Currently, the integration does **not** follow this rule. The `StiebelEltron` class in `homeassistant/components/stiebel_eltron/climate.py` is responsible for creating the climate entity. However, its `__init__` method does not set the `_attr_unique_id` attribute, nor does the class define a `unique_id` property.

Specifically, looking at the `StiebelEltron` class definition:
```python
# In homeassistant/components/stiebel_eltron/climate.py
class StiebelEltron(ClimateEntity):
    # ...
    def __init__(self, name: str, client: StiebelEltronAPI) -> None:
        """Initialize the unit."""
        self._name = name  # This sets the friendly name, not the unique ID
        self._target_temperature: float | int | None = None
        self._current_temperature: float | int | None = None
        self._current_humidity: float | int | None = None
        self._operation: str | None = None
        self._filter_alarm: bool | None = None
        self._client = client
        # No self._attr_unique_id = ... is present here.
```
And its instantiation in `async_setup_entry`:
```python
# In homeassistant/components/stiebel_eltron/climate.py
async def async_setup_entry(
    hass: HomeAssistant,
    entry: StiebelEltronConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up STIEBEL ELTRON climate platform."""
    async_add_entities([StiebelEltron(entry.title, entry.runtime_data)], True)
```
The entity is created without a unique ID.

## Suggestions

To make the `stiebel_eltron` integration compliant with the `entity-unique-id` rule, the `StiebelEltron` climate entity needs to be assigned a unique ID. A common and recommended practice is to use the `entry_id` of the `ConfigEntry` that sets up the device, as this is guaranteed to be unique.

Here's how you can modify the code:

1.  **Modify the `StiebelEltron` class `__init__` method in `homeassistant/components/stiebel_eltron/climate.py`:**
    Update the constructor to accept a `unique_id` parameter and set the `_attr_unique_id` attribute.

    ```python
    # In homeassistant/components/stiebel_eltron/climate.py

    # ... (imports and other code) ...

    class StiebelEltron(ClimateEntity):
        """Representation of a STIEBEL ELTRON heat pump."""

        _attr_hvac_modes = SUPPORT_HVAC
        _attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )
        _attr_temperature_unit = UnitOfTemperature.CELSIUS

        # Modify the constructor
        def __init__(self, name: str, unique_id: str, client: StiebelEltronAPI) -> None:
            """Initialize the unit."""
            self._name = name  # This can remain for the friendly name
            self._attr_unique_id = unique_id  # Set the unique ID
            self._target_temperature: float | int | None = None
            self._current_temperature: float | int | None = None
            self._current_humidity: float | int | None = None
            self._operation: str | None = None
            self._filter_alarm: bool | None = None
            self._client = client
        
        # ... (rest of the class) ...
    ```

2.  **Update the entity instantiation in `async_setup_entry` in `homeassistant/components/stiebel_eltron/climate.py`:**
    Pass the `entry.entry_id` as the `unique_id` when creating the `StiebelEltron` instance.

    ```python
    # In homeassistant/components/stiebel_eltron/climate.py

    # ... (imports and other code) ...

    async def async_setup_entry(
        hass: HomeAssistant,
        entry: StiebelEltronConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up STIEBEL ELTRON climate platform."""

        # Pass entry.entry_id as the unique_id
        async_add_entities(
            [StiebelEltron(entry.title, entry.entry_id, entry.runtime_data)], True
        )
    ```

**Why these changes satisfy the rule:**
*   By setting `self._attr_unique_id = unique_id` (where `unique_id` is `entry.entry_id`), each climate entity created by this integration will have a persistent and unique identifier within Home Assistant.
*   The `entry.entry_id` is unique for each configuration entry, ensuring that if multiple Stiebel Eltron devices are configured, their respective climate entities will also have unique IDs. This meets the requirement that the ID is "unique per integration domain and per platform domain."

Optionally, you could also consider using `self._attr_name = name` instead of `self._name` and removing the `name` property if it doesn't perform any custom logic, to align with common Home Assistant entity patterns. However, this is not strictly required by the `entity-unique-id` rule.

_Created at 2025-05-14 14:57:03. Prompt tokens: 6014, Output tokens: 1486, Total tokens: 11732_
