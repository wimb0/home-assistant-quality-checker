# adax: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `runtime-data` rule requires integrations to use the `ConfigEntry.runtime_data` attribute for storing data that is needed during the lifetime of the configuration entry but should not be persisted to configuration file storage. It also emphasizes using a typed `ConfigEntry` to ensure consistency and leverage type checking.

The `adax` integration **applies** this rule because it manages runtime objects (data update coordinators) that hold the state and API clients for interacting with Adax devices.

The integration **fully follows** this rule.

1.  **Usage of `ConfigEntry.runtime_data`**:
    In `__init__.py`, within the `async_setup_entry` function, the integration correctly assigns an instance of either `AdaxLocalCoordinator` or `AdaxCloudCoordinator` to `entry.runtime_data`:
    ```python
    # homeassistant/components/adax/__init__.py
    async def async_setup_entry(hass: HomeAssistant, entry: AdaxConfigEntry) -> bool:
        """Set up Adax from a config entry."""
        if entry.data.get(CONNECTION_TYPE) == LOCAL:
            local_coordinator = AdaxLocalCoordinator(hass, entry)
            entry.runtime_data = local_coordinator
        else:
            cloud_coordinator = AdaxCloudCoordinator(hass, entry)
            entry.runtime_data = cloud_coordinator

        await entry.runtime_data.async_config_entry_first_refresh()
        # ...
    ```

2.  **Typed `ConfigEntry`**:
    The integration defines a custom typed `ConfigEntry` in `coordinator.py` and uses it consistently:
    ```python
    # homeassistant/components/adax/coordinator.py
    type AdaxConfigEntry = ConfigEntry[AdaxCloudCoordinator | AdaxLocalCoordinator]
    ```
    This `AdaxConfigEntry` type is then imported and used in function signatures where the config entry is handled, such as `async_setup_entry` in both `__init__.py` and `climate.py`:
    ```python
    # homeassistant/components/adax/__init__.py
    from .coordinator import AdaxCloudCoordinator, AdaxConfigEntry, AdaxLocalCoordinator
    # ...
    async def async_setup_entry(hass: HomeAssistant, entry: AdaxConfigEntry) -> bool:
    # ...
    ```
    ```python
    # homeassistant/components/adax/climate.py
    from . import AdaxConfigEntry
    # ...
    async def async_setup_entry(
        hass: HomeAssistant,
        entry: AdaxConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
    # ...
    ```
    This ensures that `entry.runtime_data` is correctly typed as either `AdaxCloudCoordinator` or `AdaxLocalCoordinator`.

The data stored in `runtime_data` (the coordinators) are indeed runtime objects essential for the integration's operation (fetching data, interacting with the Adax API) and are not suitable for persisted storage.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:07:33. Prompt tokens: 6619, Output tokens: 805, Total tokens: 8496_
