# overkiz: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule requires integrations to use the `ConfigEntry.runtime_data` attribute for storing data that is not persisted to configuration storage but is needed during the lifetime of the configuration entry. This promotes a consistent and typed way to manage runtime data.

This rule applies to the `overkiz` integration because it manages significant runtime state that is initialized during `async_setup_entry` and used by various components of the integration. This includes the API client, data update coordinator, discovered device lists, and scenarios.

The `overkiz` integration fully follows this rule by:

1.  **Defining a typed data structure for runtime data:**
    In `homeassistant/components/overkiz/__init__.py`, a `dataclass` named `HomeAssistantOverkizData` is defined to encapsulate all runtime data:
    ```python
    @dataclass
    class HomeAssistantOverkizData:
        """Overkiz data stored in the runtime data object."""

        coordinator: OverkizDataUpdateCoordinator
        platforms: defaultdict[Platform, list[Device]]
        scenarios: list[Scenario]
    ```

2.  **Using a custom typed `ConfigEntry`:**
    A type alias `OverkizDataConfigEntry` is defined to ensure type safety when accessing `runtime_data`:
    ```python
    type OverkizDataConfigEntry = ConfigEntry[HomeAssistantOverkizData]
    ```
    This typed config entry is used consistently in function signatures, for example, in `async_setup_entry`:
    ```python
    async def async_setup_entry(hass: HomeAssistant, entry: OverkizDataConfigEntry) -> bool:
    ```

3.  **Storing runtime data in `entry.runtime_data`:**
    During `async_setup_entry`, an instance of `HomeAssistantOverkizData` is created and assigned to `entry.runtime_data`:
    ```python
    entry.runtime_data = HomeAssistantOverkizData(
        coordinator=coordinator, platforms=platforms, scenarios=scenarios
    )
    ```

4.  **Accessing runtime data correctly in other parts of the integration:**
    Platform setup files (e.g., `sensor.py`, `cover.py`, `climate.py`) and other modules like `diagnostics.py` correctly access this data via `entry.runtime_data`. For example, in `homeassistant/components/overkiz/sensor.py`:
    ```python
    async def async_setup_entry(
        hass: HomeAssistant,
        entry: OverkizDataConfigEntry, # Correctly typed entry
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up the Overkiz sensors from a config entry."""
        data = entry.runtime_data # Accessing runtime_data
        # ...
        entities.extend(
            OverkizStateSensor(
                device.device_url,
                data.coordinator, # Using data from runtime_data
                description,
            )
            # ...
        )
    ```
    Entities also access this data, typically via the `coordinator` which is part of `runtime_data`.

The `overkiz` integration's implementation is a clear and correct application of the `runtime-data` rule, promoting maintainability and type safety.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:13:38. Prompt tokens: 86959, Output tokens: 864, Total tokens: 90598_
