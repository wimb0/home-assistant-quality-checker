# wled: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `runtime-data` rule requires integrations to use the `ConfigEntry.runtime_data` attribute to store data needed during the lifetime of the configuration entry that is not persisted to storage. It also emphasizes the use of typing for this attribute, especially when `strict-typing` is implemented.

The `wled` integration **applies** to this rule as it needs to manage runtime objects like data update coordinators and API client instances associated with each configured WLED device.

The integration **fully follows** this rule.

1.  **Typed `ConfigEntry`**: In `__init__.py`, a type alias is defined:
    ```python
    type WLEDConfigEntry = ConfigEntry[WLEDDataUpdateCoordinator]
    ```
    This clearly types what `entry.runtime_data` will hold.

2.  **Storing Runtime Data**: In `__init__.py`, within the `async_setup_entry` function, an instance of `WLEDDataUpdateCoordinator` is created and assigned to `entry.runtime_data`:
    ```python
    # __init__.py
    async def async_setup_entry(hass: HomeAssistant, entry: WLEDConfigEntry) -> bool:
        """Set up WLED from a config entry."""
        entry.runtime_data = WLEDDataUpdateCoordinator(hass, entry=entry)
        await entry.runtime_data.async_config_entry_first_refresh()
        # ...
        return True
    ```
    This `WLEDDataUpdateCoordinator` instance encapsulates the WLED API client and manages data fetching for the device.

3.  **Accessing Runtime Data**: Throughout the platform setup files (e.g., `light.py`, `sensor.py`, `switch.py`, etc.), `entry.runtime_data` is consistently used to access the coordinator. The `entry` parameter in these platform `async_setup_entry` functions is correctly typed as `WLEDConfigEntry`, ensuring that `entry.runtime_data` is known to be a `WLEDDataUpdateCoordinator`.

    For example, in `sensor.py`:
    ```python
    # sensor.py
    async def async_setup_entry(
        hass: HomeAssistant,
        entry: WLEDConfigEntry, # Correctly typed
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up WLED sensor based on a config entry."""
        coordinator = entry.runtime_data # Accessing runtime_data
        async_add_entities(
            WLEDSensorEntity(coordinator, description)
            for description in SENSORS
            if description.exists_fn(coordinator.data)
        )
    ```
    This pattern is consistently followed across all relevant platform files (`button.py`, `diagnostics.py`, `light.py`, `number.py`, `select.py`, `sensor.py`, `switch.py`, `update.py`).

The integration's implementation aligns perfectly with the example and requirements outlined in the `runtime-data` rule documentation.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:28:45. Prompt tokens: 21187, Output tokens: 788, Total tokens: 23346_
