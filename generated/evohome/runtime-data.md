# evohome: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule requires integrations to use the `ConfigEntry.runtime_data` attribute to store runtime data and to do so in a typed way, typically by defining a custom `ConfigEntry` type like `MyIntegrationConfigEntry = ConfigEntry[MyRuntimeDataType]`.

The `evohome` integration **applies** to this rule because it manages runtime objects, such as the `EvoDataUpdateCoordinator`, which are necessary during the lifetime of the config entry but are not persisted to configuration storage.

The integration **partially follows** the rule:
1.  It **does** use `config_entry.runtime_data` to store the `EvoDataUpdateCoordinator` instance. This is done in `homeassistant/components/evohome/__init__.py`:
    ```python
    # homeassistant/components/evohome/__init__.py
    async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
        # ...
        coordinator = EvoDataUpdateCoordinator(
            hass, _LOGGER, config_entry=config_entry, name=f"{DOMAIN}_coordinator"
        )
        # ...
        config_entry.runtime_data = {"coordinator": coordinator} # Storing runtime data
        # ...
    ```

2.  It **does not fully** follow the "typed way" aspect as exemplified by the rule. The rule's example shows defining a type alias like `type MyIntegrationConfigEntry = ConfigEntry[MyRuntimeDataClass]` and using this specialized type in function signatures (e.g., `entry: MyIntegrationConfigEntry`). This ensures that `entry.runtime_data` itself is strongly typed.
    *   The `evohome` integration uses the generic `ConfigEntry` type in function signatures (e.g., `async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry)`).
    *   While `homeassistant/components/evohome/config_flow.py` defines an `EvoRuntimeDataT = TypedDict`, this type is:
        *   Not used to specialize the `ConfigEntry` type itself (e.g., `EvohomeConfigEntry = ConfigEntry[EvoRuntimeDataT]`).
        *   Incorrectly includes a `token_manager` field, which is not directly stored in `runtime_data` by `__init__.py` (it's part of the coordinator).
        *   Only used for casting `config_entry.runtime_data` after retrieval, rather than `config_entry.runtime_data` being inherently typed.

Accessing `runtime_data` in other files like `climate.py` and `water_heater.py` also relies on the generic `ConfigEntry` and dictionary access:
```python
# homeassistant/components/evohome/climate.py
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry, # Generic ConfigEntry
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: EvoDataUpdateCoordinator = config_entry.runtime_data["coordinator"]
```

Because the `ConfigEntry` type is not specialized (e.g., `EvohomeConfigEntry = ConfigEntry[EvohomeRuntimeData]`) and used consistently, the full benefits of static typing for `runtime_data` as per the rule's intent are not realized.

## Suggestions

To fully comply with the `runtime-data` rule, the following changes are recommended:

1.  **Define an Accurate `TypedDict` for Runtime Data:**
    Create a `TypedDict` that accurately reflects the structure stored in `config_entry.runtime_data`. This should ideally be in a shared location like `__init__.py` or a new `types.py` file.
    ```python
    # homeassistant/components/evohome/__init__.py or types.py
    from typing import TypedDict
    from homeassistant.config_entries import ConfigEntry
    from .coordinator import EvoDataUpdateCoordinator # Adjust import as necessary

    class EvohomeRuntimeData(TypedDict):
        coordinator: EvoDataUpdateCoordinator
    ```

2.  **Create a Specialized `ConfigEntry` Type Alias:**
    Use the `TypedDict` from step 1 to create a specialized `ConfigEntry` type alias.
    ```python
    # homeassistant/components/evohome/__init__.py or types.py (continued)
    EvohomeConfigEntry = ConfigEntry[EvohomeRuntimeData]
    ```

3.  **Use the Specialized `ConfigEntry` Type in Function Signatures:**
    Update function signatures across the integration to use `EvohomeConfigEntry` where `ConfigEntry` instances are handled and their `runtime_data` is accessed.
    *   In `homeassistant/components/evohome/__init__.py`:
        ```python
        async def async_setup_entry(hass: HomeAssistant, entry: EvohomeConfigEntry) -> bool:
            # ...
            coordinator = EvoDataUpdateCoordinator(...)
            entry.runtime_data = {"coordinator": coordinator} # This assignment is type-compatible
            # ...

        async def async_unload_entry(hass: HomeAssistant, entry: EvohomeConfigEntry) -> bool:
            # ...
        ```
    *   In `homeassistant/components/evohome/climate.py`:
        ```python
        async def async_setup_entry(
            hass: HomeAssistant,
            config_entry: EvohomeConfigEntry, # Use specialized type
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            coordinator = config_entry.runtime_data["coordinator"] # Access is now type-safe
            # ...
        ```
    *   In `homeassistant/components/evohome/water_heater.py`:
        ```python
        async def async_setup_entry(
            hass: HomeAssistant,
            config_entry: EvohomeConfigEntry, # Use specialized type
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            coordinator = config_entry.runtime_data["coordinator"] # Access is now type-safe
            # ...
        ```

4.  **Update or Remove `EvoRuntimeDataT` in `config_flow.py`:**
    The existing `EvoRuntimeDataT` in `config_flow.py` should be reconciled with the new `EvohomeRuntimeData`.
    *   Correct its fields (remove `token_manager` as it's not directly stored).
    *   Ideally, import and use the centrally defined `EvohomeRuntimeData` and `EvohomeConfigEntry` types if `config_entry` objects are passed to methods that need to inspect `runtime_data`.

By implementing these changes, `config_entry.runtime_data` will be strongly typed throughout the `evohome` integration, aligning with the rule's goal of consistent and typed storage for runtime data, and allowing type-checking tools to catch potential errors.

---

_Created at 2025-05-29 11:46:59. Prompt tokens: 21789, Output tokens: 1680, Total tokens: 28876._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
