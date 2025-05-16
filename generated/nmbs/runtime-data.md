# nmbs: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `runtime-data` rule mandates the use of `ConfigEntry.runtime_data` for storing data that is needed during the lifetime of a configuration entry but is not persisted to storage. This promotes consistency and enables better typing.

This rule applies to the `nmbs` integration because it sets up configuration entries and utilizes an API client (`pyrail.iRail`) for its operations. This API client instance, used by the sensors, is considered runtime data specific to the config entry.

The `nmbs` integration currently does **not** follow this rule.
1.  In `__init__.py`, the `async_setup_entry` function currently only forwards the setup to the sensor platform:
    ```python
    # __init__.py
    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Set up NMBS from a config entry."""

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    ```
    It does not initialize or store any entry-specific runtime data (like an API client) in `entry.runtime_data`.

2.  In `sensor.py`, the `async_setup_entry` function instantiates an `iRail` client:
    ```python
    # sensor.py
    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up NMBS sensor entities based on a config entry."""
        api_client = iRail(session=async_get_clientsession(hass)) # API client created here

        # ...
        station_from = find_station(hass, config_entry.data[CONF_STATION_FROM])
        station_to = find_station(hass, config_entry.data[CONF_STATION_TO])

        async_add_entities(
            [
                NMBSSensor(
                    api_client, name, show_on_map, station_from, station_to, excl_vias
                ),
                NMBSLiveBoard(
                    api_client, station_from, station_from, station_to, excl_vias
                ),
                NMBSLiveBoard(api_client, station_to, station_from, station_to, excl_vias),
            ]
        )
    ```
    This `api_client` is then passed to the sensor entities. According to the `runtime-data` rule, this `api_client` instance should be created in `__init__.py:async_setup_entry` and stored in `config_entry.runtime_data`. The platform setup (`sensor.py:async_setup_entry`) would then retrieve it from `config_entry.runtime_data`.

The integration does use `hass.data[DOMAIN]` to store a global list of all train stations, which is populated in `__init__.py:async_setup`. This global data is distinct from the per-config-entry runtime data (like the API client) that the `runtime-data` rule addresses.

## Suggestions

To make the `nmbs` integration compliant with the `runtime-data` rule, the following changes are recommended:

1.  **Define a Typed `ConfigEntry` (Recommended):**
    In `__init__.py`, define a type alias for `ConfigEntry` to specify the type of data stored in `runtime_data`. This improves type safety and clarity, as highlighted in the rule's example.

    ```python
    # __init__.py
    from pyrail import iRail
    # ... other imports ...
    from homeassistant.config_entries import ConfigEntry

    # Define the typed ConfigEntry
    type NMBSConfigEntry = ConfigEntry[iRail]
    ```
    If other runtime data were to be stored, a `dataclass` could be used as the generic type for `ConfigEntry`.

2.  **Modify `__init__.py:async_setup_entry`:**
    Instantiate the `iRail` client and store it in `entry.runtime_data`.

    ```python
    # __init__.py
    from pyrail import iRail
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    # ...
    # If NMBSConfigEntry is defined as above:
    # async def async_setup_entry(hass: HomeAssistant, entry: NMBSConfigEntry) -> bool:
    # Otherwise, use ConfigEntry and add type hint for runtime_data if possible,
    # or rely on runtime check for the type.
    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool: # Change to NMBSConfigEntry if defined
        """Set up NMBS from a config entry."""
        api_client = iRail(session=async_get_clientsession(hass))
        
        # Store the client in runtime_data
        # If using NMBSConfigEntry = ConfigEntry[iRail], this is type-checked.
        entry.runtime_data = api_client

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    ```

3.  **Modify `sensor.py:async_setup_entry`:**
    Retrieve the `api_client` from `config_entry.runtime_data` instead of creating a new instance.

    ```python
    # sensor.py
    from pyrail import iRail # Keep for type hinting if NMBSConfigEntry is not imported
    from homeassistant.config_entries import ConfigEntry # Change to NMBSConfigEntry if defined and imported
    # from . import NMBSConfigEntry # If NMBSConfigEntry is defined in __init__.py

    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry, # Change to NMBSConfigEntry if defined
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up NMBS sensor entities based on a config entry."""
        # Retrieve the api_client from runtime_data
        # If using NMBSConfigEntry: api_client: iRail = config_entry.runtime_data
        # Otherwise:
        api_client = config_entry.runtime_data 

        name = config_entry.data.get(CONF_NAME, None)
        show_on_map = config_entry.data.get(CONF_SHOW_ON_MAP, False)
        excl_vias = config_entry.data.get(CONF_EXCLUDE_VIAS, False)

        station_from = find_station(hass, config_entry.data[CONF_STATION_FROM])
        station_to = find_station(hass, config_entry.data[CONF_STATION_TO])

        async_add_entities(
            [
                NMBSSensor(
                    api_client, name, show_on_map, station_from, station_to, excl_vias
                ),
                NMBSLiveBoard(
                    api_client, station_from, station_from, station_to, excl_vias
                ),
                NMBSLiveBoard(api_client, station_to, station_from, station_to, excl_vias),
            ]
        )
    ```

4.  **Update Type Hints:**
    If the typed `NMBSConfigEntry` is introduced, ensure all usages of `ConfigEntry` that refer to an `nmbs` entry are updated to `NMBSConfigEntry` for consistency and to benefit from type checking (e.g., in `async_unload_entry`).

These changes would centralize the creation and management of the entry-specific `iRail` client in `__init__.py` and make it accessible to platforms via the standard `entry.runtime_data` mechanism, aligning the integration with the `runtime-data` rule.

_Created at 2025-05-11 07:24:52. Prompt tokens: 9445, Output tokens: 1897, Total tokens: 16209_
