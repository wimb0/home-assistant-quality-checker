# home_connect: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule requires integrations to use `ConfigEntry.runtime_data` to store runtime data, such as API client instances or data coordinators, in a typed manner. This rule applies to the `home_connect` integration as it manages an API client and coordinates data updates for multiple Home Connect appliances during its lifetime.

The integration fully follows this rule.

1.  **Typed `ConfigEntry`**:
    In `coordinator.py`, a typed `ConfigEntry` is defined:
    ```python
    type HomeConnectConfigEntry = ConfigEntry[HomeConnectCoordinator]
    ```
    This type alias is then used throughout the integration (e.g., in `__init__.py`, platform setup files like `sensor.py`, `services.py`) for type hinting `ConfigEntry` objects. This ensures that `entry.runtime_data` is correctly typed as `HomeConnectCoordinator`.

2.  **Storing Runtime Data**:
    In `__init__.py`, within the `async_setup_entry` function, the `HomeConnectCoordinator` instance is created and assigned to `entry.runtime_data`:
    ```python
    async def async_setup_entry(hass: HomeAssistant, entry: HomeConnectConfigEntry) -> bool:
        # ...
        home_connect_client = HomeConnectClient(config_entry_auth)
        coordinator = HomeConnectCoordinator(hass, entry, home_connect_client)
        await coordinator.async_setup()
        entry.runtime_data = coordinator  # <--- Rule followed here
        # ...
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        entry.runtime_data.start_event_listener() # <--- Accessing runtime_data
        # ...
        return True
    ```
    The `HomeConnectCoordinator` itself encapsulates the `HomeConnectClient` and manages the data for all connected appliances, which is a common and good practice for runtime data.

3.  **Accessing Runtime Data**:
    *   Platform setup functions (e.g., in `sensor.py`, `light.py`, `switch.py`, etc.) receive the `HomeConnectConfigEntry` and access `entry.runtime_data` to pass the coordinator to the entities they create. For example, in `sensor.py`:
        ```python
        def _get_entities_for_appliance(
            entry: HomeConnectConfigEntry,
            appliance: HomeConnectApplianceData,
        ) -> list[HomeConnectEntity]:
            return [
                HomeConnectProgramSensor(entry.runtime_data, appliance, desc)
                # ...
            ]
        ```
    *   Services defined in `services.py` also correctly retrieve the coordinator (and subsequently the client) from `entry.runtime_data`:
        ```python
        async def _get_client_and_ha_id(
            hass: HomeAssistant, device_id: str
        ) -> tuple[HomeConnectClient, str]:
            # ...
            # entry is retrieved and is of type HomeConnectConfigEntry
            # ...
            return entry.runtime_data.client, ha_id
        ```
    *   Diagnostic functions in `diagnostics.py` access `entry.runtime_data.data` to retrieve appliance information.

The integration's approach aligns with the rule's example and reasoning, promoting consistency and type safety for runtime data management.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 20:27:21. Prompt tokens: 139044, Output tokens: 877, Total tokens: 142088_
