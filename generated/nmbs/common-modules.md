# nmbs: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule mandates that common Home Assistant patterns, specifically data update coordinators and base entities, should be placed in designated files (`coordinator.py` and `entity.py`, respectively) to enhance consistency and maintainability.

This rule applies to the `nmbs` integration because:
1.  It fetches data from an external API (`pyrail`) to update its sensor states. This is a prime use case for the `DataUpdateCoordinator` pattern.
2.  It provides multiple sensor entity types (`NMBSSensor` and `NMBSLiveBoard`). These entities share some common characteristics and behaviors, making them suitable for a common base entity class.

The `nmbs` integration currently does **not** follow this rule:

1.  **No Coordinator (`coordinator.py`):**
    The integration does not use the `DataUpdateCoordinator` pattern. Instead, data fetching is performed independently within the `async_update` method of each sensor entity. For example, in `sensor.py`:
    *   `NMBSSensor.async_update` calls `self._api_client.get_connections(...)`.
    *   `NMBSLiveBoard.async_update` calls `self._api_client.get_liveboard(...)`.
    There is no `coordinator.py` file, and no `DataUpdateCoordinator` subclass is defined or used to centralize these data fetching operations.

2.  **No Base Entity (`entity.py`):**
    The `NMBSSensor` and `NMBSLiveBoard` entities in `sensor.py` inherit directly from the generic `SensorEntity` class. While they share common attributes (e.g., `_attr_attribution = "https://api.irail.be/"`) and some similar logic (e.g., icon updates based on delays), there is no common base entity class (e.g., `NMBSEntity`) defined within the integration. Consequently, there is no `entity.py` file.

By not adopting these common patterns and their prescribed file locations, the integration misses opportunities for code centralization, reduced duplication, and improved adherence to Home Assistant's best practices for integration structure.

## Suggestions

To make the `nmbs` integration compliant with the `common-modules` rule and improve its structure, the following changes are recommended:

1.  **Implement Data Update Coordinators (`coordinator.py`):**
    *   Create a new file named `coordinator.py` in the `nmbs` integration directory.
    *   Define `DataUpdateCoordinator` subclasses in this file to manage data fetching for the different API endpoints. Given that a config entry can result in fetching connection data and two separate liveboard data sets, you might need multiple coordinators or one coordinator managing combined data:
        *   A `NMBSConnectionCoordinator` for fetching data from `api_client.get_connections()`.
        *   An `NMBSLiveBoardCoordinator` for fetching data from `api_client.get_liveboard()`. You'll likely instantiate this twice per config entry, once for the departure station and once for the arrival station if liveboards for both are desired.

    *Example structure for `coordinator.py`:*
    ```python
    # nmbs/coordinator.py
    import logging
    from datetime import timedelta

    from pyrail import iRail
    from pyrail.models import ConnectionDetails, LiveboardDeparture # Adjust based on actual return types

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

    from .const import DOMAIN # Make sure DOMAIN is accessible

    LOGGER = logging.getLogger(__name__)

    class NMBSConnectionCoordinator(DataUpdateCoordinator[ConnectionDetails]): # Type hint with actual data type
        """Coordinator for NMBS connection data."""

        def __init__(self, hass: HomeAssistant, api_client: iRail, station_from_id: str, station_to_id: str):
            """Initialize coordinator."""
            super().__init__(
                hass,
                LOGGER,
                name=f"{DOMAIN}_connection_{station_from_id}_{station_to_id}",
                update_interval=timedelta(minutes=2),  # Adjust as appropriate
            )
            self.api_client = api_client
            self.station_from_id = station_from_id
            self.station_to_id = station_to_id

        async def _async_update_data(self) -> ConnectionDetails:
            """Fetch data from API endpoint."""
            # Original logic from NMBSSensor.async_update for get_connections
            # and selecting the relevant connection would go here.
            connections = await self.api_client.get_connections(
                self.station_from_id, self.station_to_id
            )
            if connections is None or not connections.connections:
                raise UpdateFailed("Failed to retrieve connection data or no connections found")
            
            # Logic to determine the specific connection to return (e.g., next_connection)
            # This is simplified; refer to current logic in NMBSSensor
            relevant_connection = connections.connections[0]
            if hasattr(relevant_connection.departure, 'left') and relevant_connection.departure.left and len(connections.connections) > 1:
                relevant_connection = connections.connections[1]
            return relevant_connection


    class NMBSLiveBoardCoordinator(DataUpdateCoordinator[LiveboardDeparture]): # Type hint with actual data type
        """Coordinator for NMBS liveboard data."""

        def __init__(self, hass: HomeAssistant, api_client: iRail, station_id: str):
            """Initialize coordinator."""
            super().__init__(
                hass,
                LOGGER,
                name=f"{DOMAIN}_liveboard_{station_id}",
                update_interval=timedelta(minutes=1),  # Adjust as appropriate
            )
            self.api_client = api_client
            self.station_id = station_id

        async def _async_update_data(self) -> LiveboardDeparture: # Assuming one departure is primary
            """Fetch data from API endpoint."""
            # Original logic from NMBSLiveBoard.async_update for get_liveboard
            # and selecting the relevant departure would go here.
            liveboard = await self.api_client.get_liveboard(self.station_id)
            if liveboard is None or not liveboard.departures:
                raise UpdateFailed("Failed to retrieve liveboard data or no departures found")
            return liveboard.departures[0] # Example: return the next departure
    ```

    *   In `sensor.py` (or `__init__.py` during `async_setup_entry`), instantiate these coordinators, pass the `api_client`, and perform an initial refresh (e.g., `await coordinator.async_config_entry_first_refresh()`).
    *   The `api_client` currently created in `sensor.py`'s `async_setup_entry` should be passed to these coordinators.

2.  **Create a Base Entity Class (`entity.py`):**
    *   Create a new file named `entity.py` in the `nmbs` integration directory.
    *   Define a base entity class, e.g., `NMBSEntity`, that inherits from `CoordinatorEntity`.
    *   Move common attributes like `_attr_attribution` and shared `device_info` logic into this base class.

    *Example structure for `entity.py`:*
    ```python
    # nmbs/entity.py
    from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
    from homeassistant.helpers.device_registry import DeviceInfo
    from .const import DOMAIN # Make sure DOMAIN is accessible

    class NMBSEntity(CoordinatorEntity[DataUpdateCoordinator]): # Use a more specific Coordinator type if possible
        """Base class for NMBS entities."""

        _attr_attribution = "https://api.irail.be/"
        # _attr_has_entity_name = True # Consider if appropriate

        def __init__(self, coordinator: DataUpdateCoordinator, config_entry_id: str, name_suffix: str):
            """Initialize the NMBS entity."""
            super().__init__(coordinator)
            # Example: link all entities from one config entry to one device
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, config_entry_id)},
                name=f"NMBS Route {name_suffix}", # Or a name based on the config entry title
                manufacturer="NMBS/SNCB (via iRail)",
                model="iRail API Data",
            )
            # Unique ID might be better set in the derived classes
            # self._attr_unique_id = f"{config_entry_id}_{coordinator.name}"
    ```

3.  **Refactor Entities to Use Coordinator and Base Entity:**
    *   In `sensor.py`, modify `NMBSSensor` and `NMBSLiveBoard` to inherit from your new base entity (e.g., `NMBSEntity`).
    *   Pass the appropriate coordinator instance to each entity during initialization.
    *   Remove the `async_update` methods from the individual entities; they will now rely on the coordinator for data updates.
    *   Access data via `self.coordinator.data` within the entities.

    *Example snippet for refactoring `NMBSSensor` in `sensor.py`*:
    ```python
    # nmbs/sensor.py (partial)
    # from .coordinator import NMBSConnectionCoordinator # Import coordinator
    # from .entity import NMBSEntity # Import base entity

    class NMBSSensor(NMBSEntity, SensorEntity): # Inherit from base and SensorEntity
        """NMBS connection sensor."""
        # _attr_native_unit_of_measurement = UnitOfTime.MINUTES (already there)

        def __init__(
            self,
            coordinator: NMBSConnectionCoordinator, # Pass the specific coordinator
            config_entry: ConfigEntry, # To get original name, options, and entry_id
            station_from: StationDetails, # For naming or specific logic if needed
            station_to: StationDetails,
        ):
            """Initialize the sensor."""
            # Construct a unique name suffix for the device, or use config_entry.title
            device_name_suffix = f"{station_from.standard_name} to {station_to.standard_name}"
            super().__init__(coordinator, config_entry.entry_id, device_name_suffix)
            
            # Set unique ID and name
            vias = "_excl_vias" if config_entry.data.get(CONF_EXCLUDE_VIAS) else ""
            self._attr_unique_id = f"nmbs_connection_{station_from.id}_{station_to.id}{vias}"
            
            custom_name = config_entry.data.get(CONF_NAME)
            if custom_name:
                self._attr_name = custom_name
            else:
                self._attr_name = f"Train from {station_from.standard_name} to {station_to.standard_name}"

            self._show_on_map = config_entry.data.get(CONF_SHOW_ON_MAP, False)
            self._excl_vias = config_entry.data.get(CONF_EXCLUDE_VIAS, False)


        @property
        def native_value(self) -> int | None:
            """Return the state of the device."""
            if self.coordinator.data is None:
                return None
            
            connection_data = self.coordinator.data # Type: ConnectionDetails
            
            # Logic from old async_update to calculate duration, now using coordinator.data
            # Ensure self._excl_vias and self.is_via_connection checks are handled appropriately
            if self._excl_vias and self.is_via_connection: # is_via_connection would now use self.coordinator.data
                 return None # Or previous state if preferred for skipped updates

            return get_ride_duration(
                connection_data.departure.time,
                connection_data.arrival.time,
                connection_data.departure.delay,
            )
        
        # Other properties (icon, extra_state_attributes) would be updated
        # to use self.coordinator.data (which holds a ConnectionDetails object)
        # For example, self._attrs would become self.coordinator.data
    ```
    A similar refactoring would apply to `NMBSLiveBoard`.

By implementing these changes, the `nmbs` integration will align with the `common-modules` rule, leading to a more robust, maintainable, and standardized codebase. This also centralizes API calls, potentially reducing redundant requests and making error handling more consistent.

_Created at 2025-05-11 07:20:20. Prompt tokens: 9265, Output tokens: 2988, Total tokens: 18025_
