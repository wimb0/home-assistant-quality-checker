# stiebel_eltron: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule requires that common patterns like data update coordinators be placed in `coordinator.py` and base entities in `entity.py`. This rule applies to the `stiebel_eltron` integration as it involves polling a device for data, a pattern ideally suited for a `DataUpdateCoordinator`.

The integration currently does **not** follow this rule:

1.  **No `DataUpdateCoordinator` is used:**
    The integration fetches data directly within its climate entity. In `climate.py`, the `StiebelEltron` class has an `update()` method:
    ```python
    # climate.py
    class StiebelEltron(ClimateEntity):
        # ...
        def update(self) -> None:
            """Update unit attributes."""
            self._client.update() # Synchronous data fetching
            # ...
    ```
    This `self._client.update()` call is a synchronous, blocking I/O operation. This pattern should be handled by a `DataUpdateCoordinator` to manage polling and run blocking I/O in an executor thread.

2.  **No `coordinator.py` file:**
    Since a `DataUpdateCoordinator` is not used, the corresponding `coordinator.py` file, where such a coordinator class should be defined, does not exist.

3.  **No `entity.py` file for a base entity:**
    While the integration currently only provides a `climate` platform, if a `DataUpdateCoordinator` were introduced, the `StiebelEltron` climate entity would typically inherit from `CoordinatorEntity`. A common practice is to define a base entity class (e.g., `StiebelEltronBaseEntity`) in `entity.py` that itself inherits from `CoordinatorEntity`. This base class would handle common aspects like `device_info` and accessing coordinator data. This file and pattern are currently missing.

The absence of these common modules and patterns means the integration does not adhere to the best practices for consistency and maintainability outlined by the `common-modules` rule.

## Suggestions

To make the `stiebel_eltron` integration compliant with the `common-modules` rule, the following changes are recommended:

1.  **Create `coordinator.py` and implement `StiebelEltronDataUpdateCoordinator`:**
    *   Create a new file: `homeassistant/components/stiebel_eltron/coordinator.py`.
    *   Define a class `StiebelEltronDataUpdateCoordinator` that inherits from `homeassistant.helpers.update_coordinator.DataUpdateCoordinator`.
    *   This coordinator will manage the `StiebelEltronAPI` client and handle data fetching.

    ```python
    # homeassistant/components/stiebel_eltron/coordinator.py
    import logging
    from datetime import timedelta

    from pystiebeleltron.pystiebeleltron import StiebelEltronAPI # Or relevant data type

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

    from .const import DOMAIN

    _LOGGER = logging.getLogger(__name__)

    class StiebelEltronDataUpdateCoordinator(DataUpdateCoordinator[StiebelEltronAPI]): # Or dict/custom data type
        """Class to manage fetching STIEBEL ELTRON data."""

        def __init__(self, hass: HomeAssistant, client: StiebelEltronAPI, name: str) -> None:
            """Initialize global STIEBEL ELTRON data updater."""
            self.api = client
            super().__init__(
                hass,
                _LOGGER,
                name=f"{DOMAIN} {name}",
                update_interval=timedelta(seconds=60), # Adjust as needed
            )

        async def _async_update_data(self) -> StiebelEltronAPI: # Or dict/custom data type
            """Fetch data from API."""
            try:
                # self.api.update() is blocking, so run in executor
                # Assuming self.api.update() returns True/False and data is accessed via getters
                if not await self.hass.async_add_executor_job(self.api.update):
                    raise UpdateFailed("Failed to update data from Stiebel Eltron device")
                # Return the client itself, or a dict of relevant data
                return self.api
            except Exception as err:
                raise UpdateFailed(f"Error communicating with API: {err}") from err
    ```

2.  **Update `__init__.py` to use the coordinator:**
    *   In `async_setup_entry`, instantiate `StiebelEltronDataUpdateCoordinator`.
    *   Perform an initial refresh using `await coordinator.async_config_entry_first_refresh()`.
    *   Store the coordinator instance in `entry.runtime_data` (replacing the current client).

    ```python
    # homeassistant/components/stiebel_eltron/__init__.py
    # ...
    from .coordinator import StiebelEltronDataUpdateCoordinator
    # ...

    async def async_setup_entry(
        hass: HomeAssistant, entry: StiebelEltronConfigEntry # Update StiebelEltronConfigEntry type hint
    ) -> bool:
        """Set up STIEBEL ELTRON from a config entry."""
        client = StiebelEltronAPI(
            ModbusTcpClient(entry.data[CONF_HOST], port=entry.data[CONF_PORT]), 1
        )

        coordinator = StiebelEltronDataUpdateCoordinator(hass, client, entry.title)
        await coordinator.async_config_entry_first_refresh() # This will raise ConfigEntryNotReady on failure

        entry.runtime_data = coordinator # Store coordinator

        await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
        return True

    # Update type hint for ConfigEntry
    # type StiebelEltronConfigEntry = ConfigEntry[StiebelEltronDataUpdateCoordinator]
    ```

3.  **Create `entity.py` for a base entity (optional but recommended):**
    *   Create a new file: `homeassistant/components/stiebel_eltron/entity.py`.
    *   Define a base class `StiebelEltronEntity` that inherits from `CoordinatorEntity`.

    ```python
    # homeassistant/components/stiebel_eltron/entity.py
    from homeassistant.helpers.entity import DeviceInfo
    from homeassistant.helpers.update_coordinator import CoordinatorEntity

    from .const import DOMAIN
    from .coordinator import StiebelEltronDataUpdateCoordinator

    class StiebelEltronEntity(CoordinatorEntity[StiebelEltronDataUpdateCoordinator]):
        """Base class for STIEBEL ELTRON entities."""

        _attr_has_entity_name = True

        def __init__(self, coordinator: StiebelEltronDataUpdateCoordinator) -> None:
            """Initialize the entity."""
            super().__init__(coordinator)
            # Example: Set up device info. Adjust identifier/name as needed.
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.api.some_unique_id_or_host)}, # Requires API to expose unique ID or use host
                name=coordinator.name,
                manufacturer="STIEBEL ELTRON",
                # model=coordinator.api.get_model(), # If available
                # sw_version=coordinator.api.get_firmware_version(), # If available
            )
    ```

4.  **Refactor `climate.py` to use the coordinator and base entity:**
    *   The `StiebelEltron` climate entity should inherit from `StiebelEltronEntity` (or `CoordinatorEntity` directly if `entity.py` is skipped for now).
    *   Remove the custom `update()` method. Data will be sourced from `self.coordinator.data` (which would be the `StiebelEltronAPI` client instance or the data it returned).
    *   Update `__init__` to accept the coordinator.
    *   Modify `async_setup_entry` in `climate.py` to get the coordinator from `entry.runtime_data`.

    ```python
    # homeassistant/components/stiebel_eltron/climate.py
    # ...
    from homeassistant.helpers.update_coordinator import CoordinatorEntity # If not using StiebelEltronEntity

    # from .entity import StiebelEltronEntity # If using StiebelEltronEntity
    from .coordinator import StiebelEltronDataUpdateCoordinator

    # Adjust StiebelEltronConfigEntry to use the coordinator type
    # from . import StiebelEltronConfigEntry -> This type is defined in __init__.py
    # and its generic type should be updated there.

    async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry, # Use generic ConfigEntry or updated StiebelEltronConfigEntry
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up STIEBEL ELTRON climate platform."""
        coordinator: StiebelEltronDataUpdateCoordinator = entry.runtime_data
        async_add_entities([StiebelEltronClimate(coordinator)], True) # Pass coordinator

    # class StiebelEltronClimate(StiebelEltronEntity): # If using base entity
    class StiebelEltronClimate(CoordinatorEntity[StiebelEltronDataUpdateCoordinator]):
        """Representation of a STIEBEL ELTRON heat pump."""
        _attr_hvac_modes = SUPPORT_HVAC
        _attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )
        _attr_temperature_unit = UnitOfTemperature.CELSIUS
        _attr_name = None # Use has_entity_name = True for device-centric naming
        _attr_has_entity_name = True


        def __init__(self, coordinator: StiebelEltronDataUpdateCoordinator) -> None:
            """Initialize the unit."""
            # super().__init__(coordinator) # If using StiebelEltronEntity, it calls this
            super().__init__(coordinator) # If directly inheriting CoordinatorEntity
            self._attr_unique_id = f"{coordinator.config_entry.entry_id}_climate" # Example unique ID
            # Device info can be set here or in a base entity
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
                name=coordinator.name, # or entry.title
                manufacturer="STIEBEL ELTRON",
            )
            # No self._client needed, use self.coordinator.api or self.coordinator.data

        # Remove the update(self) method entirely

        # Access data via self.coordinator.data (which is the API client instance in this example)
        # or self.coordinator.api
        # Example:
        # @property
        # def current_temperature(self) -> float | None:
        #     return self.coordinator.data.get_current_temp()

        # Properties like target_temperature, current_temperature, etc.,
        # need to be updated to use self.coordinator.data.get_...()
        # For example:
        @property
        def target_temperature(self) -> float | None:
            """Return the temperature we try to reach."""
            return self.coordinator.data.get_target_temp()

        @property
        def current_temperature(self) -> float | None:
            """Return the current temperature."""
            return self.coordinator.data.get_current_temp()

        # ... and so on for other properties

        # Service calls would still use the API client, possibly via coordinator
        def set_temperature(self, **kwargs: Any) -> None:
            """Set new target temperature."""
            target_temperature = kwargs.get(ATTR_TEMPERATURE)
            if target_temperature is not None:
                _LOGGER.debug("set_temperature: %s", target_temperature)
                # self.coordinator.data is the API client here
                self.coordinator.data.set_target_temp(target_temperature)
                self.async_write_ha_state() # Request an update after changing state

        # Similar changes for set_hvac_mode, set_preset_mode
        # ... ensure to call self.async_write_ha_state() after commands
        # or better, await coordinator.async_request_refresh() if the device state needs to be re-read
    ```

These changes will centralize data fetching, make it asynchronous, improve error handling, and align the integration with Home Assistant's common architectural patterns, thus satisfying the `common-modules` rule. Remember to adjust type hints for `ConfigEntry` and data types as needed.

_Created at 2025-05-14 14:54:34. Prompt tokens: 6026, Output tokens: 3001, Total tokens: 12480_
