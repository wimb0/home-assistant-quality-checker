# adax: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unique-id` rule requires that all entities created by an integration have a unique ID. This allows Home Assistant to track entities across restarts and enables users to customize them (e.g., rename, change area). This rule applies to the `adax` integration as it creates `climate` entities for Adax heaters.

The `adax` integration correctly implements unique IDs for its entities in both its connection modes (Cloud and Local):

1.  **Cloud Connected Devices (`AdaxDevice`)**:
    For devices connected via the Adax cloud, the unique ID is generated in the `__init__` method of the `AdaxDevice` class in `climate.py`:
    ```python
    # homeassistant/components/adax/climate.py
    class AdaxDevice(CoordinatorEntity[AdaxCloudCoordinator], ClimateEntity):
        # ...
        def __init__(
            self,
            coordinator: AdaxCloudCoordinator,
            device_id: str,
        ) -> None:
            # ...
            self._attr_unique_id = f"{self.room['homeId']}_{self._device_id}"
            # ...
    ```
    Here, `self.room['homeId']` and `self._device_id` are properties obtained from the Adax cloud API. This combination ensures a unique and stable identifier for each cloud-managed heater entity.

2.  **Locally Connected Devices (`LocalAdaxDevice`)**:
    For devices connected locally, the unique ID is also set in the `__init__` method of the `LocalAdaxDevice` class in `climate.py`:
    ```python
    # homeassistant/components/adax/climate.py
    class LocalAdaxDevice(CoordinatorEntity[AdaxLocalCoordinator], ClimateEntity):
        # ...
        def __init__(self, coordinator: AdaxLocalCoordinator, unique_id: str) -> None:
            """Initialize the heater."""
            super().__init__(coordinator)
            self._adax_data_handler: AdaxLocal = coordinator.adax_data_handler
            self._attr_unique_id = unique_id # This is the unique ID
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, unique_id)},
                manufacturer="Adax",
            )
    ```
    This `unique_id` is passed to the constructor during entity setup:
    ```python
    # homeassistant/components/adax/climate.py
    async def async_setup_entry(
        # ...
    ) -> None:
        # ...
        if entry.data.get(CONNECTION_TYPE) == LOCAL:
            local_coordinator = cast(AdaxLocalCoordinator, entry.runtime_data)
            async_add_entities(
                [LocalAdaxDevice(local_coordinator, entry.data[CONF_UNIQUE_ID])], # unique_id from entry.data
            )
        # ...
    ```
    The `entry.data[CONF_UNIQUE_ID]` is established during the configuration flow (`config_flow.py`). For local devices, this ID is derived from the device's MAC address:
    ```python
    # homeassistant/components/adax/config_flow.py
    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # ...
        unique_id = str(configurator.mac_id) # MAC address as unique_id
        await self.async_set_unique_id(unique_id)
        # ...
        return self.async_create_entry(
            title=unique_id,
            data={
                # ...
                CONF_UNIQUE_ID: unique_id, # Stored in config entry data
                CONNECTION_TYPE: LOCAL,
            },
        )
    ```
    Using the MAC address provides a highly reliable and unique identifier for locally controlled heaters.

In both cases, the `adax` integration assigns a stable and unique `_attr_unique_id` to its climate entities, thereby fully complying with the `entity-unique-id` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:06:20. Prompt tokens: 6562, Output tokens: 1054, Total tokens: 10303_
