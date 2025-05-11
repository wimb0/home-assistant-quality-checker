# wled: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unavailable` rule states that if an integration can't fetch data from a device or service, its entities should be marked as unavailable. If data can be fetched but some pieces are missing, the entity state should be unknown.

The `wled` integration utilizes the `DataUpdateCoordinator` pattern for managing data updates from WLED devices and GitHub for release information.

1.  **Coordinator Implementation (`coordinator.py`):**
    *   Both `WLEDDataUpdateCoordinator` (for device data) and `WLEDReleasesDataUpdateCoordinator` (for firmware releases) inherit from `DataUpdateCoordinator`.
    *   In `WLEDDataUpdateCoordinator._async_update_data`, if a `WLEDError` occurs during the API call to `self.wled.update()`, an `UpdateFailed` exception is raised:
        ```python
        # coordinator.py
        async def _async_update_data(self) -> WLEDDevice:
            """Fetch data from WLED."""
            try:
                device = await self.wled.update()
            except WLEDError as error:
                raise UpdateFailed(f"Invalid response from API: {error}") from error
            # ...
            return device
        ```
    *   Similarly, `WLEDReleasesDataUpdateCoordinator._async_update_data` raises `UpdateFailed` for `WLEDError` when fetching releases.
    *   Raising `UpdateFailed` correctly signals to the `DataUpdateCoordinator` that the update failed, which in turn sets its `last_update_success` property to `False`.
    *   The WebSocket listener in `WLEDDataUpdateCoordinator` also explicitly sets `self.last_update_success = False` upon `WLEDConnectionClosedError` or `WLEDError` during the listen phase.

2.  **Entity Implementation (e.g., `entity.py`, `light.py`, `sensor.py`):**
    *   The base `WLEDEntity` (in `entity.py`) inherits from `CoordinatorEntity`. The `CoordinatorEntity` class provides a default `available` property that checks `self.coordinator.last_update_success`. This means entities will automatically become unavailable if the coordinator fails to update.
        ```python
        # homeassistant/helpers/update_coordinator.py (CoordinatorEntity)
        @property
        def available(self) -> bool:
            """Return if entity is available."""
            return self._attr_available and self.coordinator.last_update_success
        ```
    *   Entities that define their own `available` property (e.g., `WLEDMainLight`, `WLEDSegmentLight` in `light.py`, `WLEDUpdateEntity` in `update.py`, `WLEDReverseSwitch` in `switch.py`, `WLEDPresetSelect` in `select.py`) consistently include `super().available` in their logic. This ensures that the coordinator's availability is always respected, and additional checks are for entity-specific conditions (like a segment not existing or no presets being available).
        For example, in `light.py` for `WLEDSegmentLight`:
        ```python
        @property
        def available(self) -> bool:
            """Return True if entity is available."""
            try:
                self.coordinator.data.state.segments[self._segment]
            except KeyError:
                return False
            return super().available
        ```
        And in `update.py` for `WLEDUpdateEntity`:
        ```python
        @property
        def available(self) -> bool:
            """Return if entity is available."""
            return super().available and self.releases_coordinator.last_update_success
        ```
    *   For sensors in `sensor.py`, if specific data points are missing (e.g., WiFi info), the `value_fn` returns `None`. When the coordinator update itself is successful, this correctly leads to an `unknown` state for the sensor, as per the rule.

3.  **Command Exception Handling (`helpers.py`):**
    *   The `wled_exception_handler` decorator used for entity commands (like `async_turn_on`) catches `WLEDConnectionError`. In such cases, it sets `self.coordinator.last_update_success = False` and calls `self.coordinator.async_update_listeners()`. This ensures that entities become unavailable if communication fails during a command execution, even before the next scheduled coordinator update.

The combination of `DataUpdateCoordinator` raising `UpdateFailed`, `CoordinatorEntity`'s default availability logic, and the correct chaining of `super().available` in custom availability properties ensures that WLED entities are marked unavailable when the device or service is unreachable. Partial data issues leading to `unknown` states are also handled correctly.

Therefore, the integration fully follows the `entity-unavailable` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:54:37. Prompt tokens: 22341, Output tokens: 1195, Total tokens: 26096_
