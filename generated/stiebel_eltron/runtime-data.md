# stiebel_eltron: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule mandates the use of `ConfigEntry.runtime_data` for storing data needed during the lifetime of a configuration entry but not persisted to storage. It also encourages typed storage for consistency and to leverage type checking.

This rule applies to the `stiebel_eltron` integration because it initializes and uses a client object (`StiebelEltronAPI`) to communicate with the device. This client is essential for the integration's operation throughout its lifecycle.

The `stiebel_eltron` integration correctly follows this rule.

1.  **Typed `ConfigEntry` Definition:**
    In `homeassistant/components/stiebel_eltron/__init__.py`, a specific type alias for the `ConfigEntry` is defined, incorporating the type of the runtime data:
    ```python
    type StiebelEltronConfigEntry = ConfigEntry[StiebelEltronAPI]
    ```
    This makes `entry.runtime_data` explicitly typed as `StiebelEltronAPI`.

2.  **Storing Runtime Data:**
    In `async_setup_entry` within `homeassistant/components/stiebel_eltron/__init__.py`, the `StiebelEltronAPI` client is instantiated and then stored in `entry.runtime_data`:
    ```python
    async def async_setup_entry(
        hass: HomeAssistant, entry: StiebelEltronConfigEntry
    ) -> bool:
        """Set up STIEBEL ELTRON from a config entry."""
        client = StiebelEltronAPI(
            ModbusTcpClient(entry.data[CONF_HOST], port=entry.data[CONF_PORT]), 1
        )
        # ... connection check ...
        entry.runtime_data = client # Storing the client
        # ...
        return True
    ```

3.  **Using Typed `ConfigEntry`:**
    The custom `StiebelEltronConfigEntry` type is used consistently in function signatures where the config entry is handled, for example:
    -   `async_setup_entry(hass: HomeAssistant, entry: StiebelEltronConfigEntry)` in `__init__.py`
    -   `async_unload_entry(hass: HomeAssistant, entry: StiebelEltronConfigEntry)` in `__init__.py`
    -   `async_setup_entry(hass: HomeAssistant, entry: StiebelEltronConfigEntry, ...)` in `climate.py`

4.  **Accessing Runtime Data in Platforms:**
    In platform setup, specifically in `homeassistant/components/stiebel_eltron/climate.py`, the `runtime_data` is accessed from the typed entry to pass the client to the entity:
    ```python
    from . import StiebelEltronConfigEntry # Importing the typed entry

    async def async_setup_entry(
        hass: HomeAssistant,
        entry: StiebelEltronConfigEntry, # Using the typed entry
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up STIEBEL ELTRON climate platform."""
        # Accessing entry.runtime_data which is type-hinted as StiebelEltronAPI
        async_add_entities([StiebelEltron(entry.title, entry.runtime_data)], True)
    ```
    The `StiebelEltron` climate entity's `__init__` method also correctly types the received client:
    ```python
    class StiebelEltron(ClimateEntity):
        # ...
        def __init__(self, name: str, client: StiebelEltronAPI) -> None:
            """Initialize the unit."""
            # ...
            self._client = client
    ```

The integration adheres to all aspects of the `runtime-data` rule by using `entry.runtime_data` and implementing the recommended typing for it.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 14:58:43. Prompt tokens: 6071, Output tokens: 977, Total tokens: 8805_
