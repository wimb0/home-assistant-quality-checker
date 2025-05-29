# evohome: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unavailable` rule states that an integration should mark its entities as unavailable if data cannot be fetched from the device or service. If data can be fetched but specific pieces are missing, the relevant entity states should be marked as unknown.

This rule applies to the `evohome` integration as it polls a cloud service for data and uses the `DataUpdateCoordinator` and `CoordinatorEntity` pattern, which is explicitly mentioned in the rule.

The `evohome` integration partially follows this rule:

1.  **Coordinator-level unavailability (Done):**
    The `EvoDataUpdateCoordinator` in `coordinator.py` (specifically in `_async_update_data` via `_update_v2_api_state`) correctly raises `UpdateFailed` if the main API calls to the Evohome cloud service fail (e.g., due to network issues, API errors, or rate limiting). Since all entities (`EvoController`, `EvoZone`, `EvoDHW`) inherit from `CoordinatorEntity` (via `EvoEntity`) and do not override the `available` property in a way that bypasses this, they will correctly become unavailable if the coordinator fails to update (i.e., `self.coordinator.last_update_success` becomes `False`). This is handled by the base `CoordinatorEntity.available` property.

2.  **Entity-specific unavailability (Todo):**
    The rule also implies that if the coordinator update is successful overall, but data for a *specific* entity is missing from the successful response, that specific entity should become unavailable. The example provided in the rule is `return super().available and self.identifier in self.coordinator.data`.
    Currently, `EvoZone` (for heating zones) and `EvoDHW` (for domestic hot water) entities do not implement such a check. If the Evohome API returns a successful response but omits data for a particular zone or the DHW system, these entities will remain `available` (because `super().available` is true) and may display stale data.
    *   For `EvoZone` entities (in `climate.py`): They rely on `self._evo_device` (an `evohomeasync2.Zone` object). The `evohomeasync2` library updates the list of zones (`self.coordinator.tcs.zones`) based on the latest API response. If a zone is no longer in the response, its corresponding `evohomeasync2.Zone` object will not be in the *current* `self.coordinator.tcs.zones` list. The HA entity should reflect this by becoming unavailable.
    *   For the `EvoDHW` entity (in `water_heater.py`): Similarly, it relies on `self._evo_device` (an `evohomeasync2.HotWater` object). If DHW data is missing in an update, the `self.coordinator.tcs.hotwater` property (from `evohomeasync2`) will become `None`. The `EvoDHW` entity should become unavailable in this case.

3.  **Missing pieces of data (Mostly Done):**
    If a specific piece of data for an entity is missing (e.g., high-precision temperature from the v1 API via `_update_v1_api_temps` in `coordinator.py`, or a standard temperature reading is `None`), the integration generally handles this by falling back to other data sources or returning `None` for the property (e.g., `EvoChild.current_temperature`). Home Assistant typically renders a `None` state as "Unknown", which aligns with this part of the rule. The `_update_v1_api_temps` method itself does not raise `UpdateFailed` for v1 API issues, which is acceptable as v2 is the primary data source, and missing v1 data is "missing a few pieces".

Because child entities (`EvoZone`, `EvoDHW`) do not become unavailable when their specific data is missing from an otherwise successful coordinator update, the integration does not fully follow the rule.

## Suggestions

To make the `evohome` integration fully compliant with the `entity-unavailable` rule, the following changes are recommended:

1.  **Implement `available` property for `EvoZone`:**
    In `homeassistant/components/evohome/climate.py`, modify the `EvoZone` class:

    ```python
    class EvoZone(EvoChild, EvoClimateEntity):
        # ... existing code ...

        @property
        def available(self) -> bool:
            """Return True if entity is available."""
            if not super().available:  # Checks coordinator's last_update_success
                return False
            # Check if this zone's underlying evohomeasync2.Zone object
            # is still present in the coordinator's current list of active zones.
            # The `self.coordinator.tcs.zones` list is updated by evohomeasync2
            # based on the zones actually present in the latest successful API response.
            return self._evo_device in self.coordinator.tcs.zones
    ```
    This ensures that an `EvoZone` entity becomes unavailable if its data is not part of the latest successful update from the coordinator, even if the coordinator itself successfully fetched data for other parts of the system.

2.  **Implement `available` property for `EvoDHW`:**
    In `homeassistant/components/evohome/water_heater.py`, modify the `EvoDHW` class:

    ```python
    class EvoDHW(EvoChild, WaterHeaterEntity):
        # ... existing code ...

        @property
        def available(self) -> bool:
            """Return True if entity is available."""
            if not super().available:  # Checks coordinator's last_update_success
                return False
            # The `self.coordinator.tcs.hotwater` property from evohomeasync2
            # will be the specific DHW device object if DHW data was present in the
            # last successful update, or None otherwise.
            # We check if our entity's device object (`self._evo_device`) matches
            # the one currently reported by the coordinator.
            return self.coordinator.tcs.hotwater == self._evo_device
    ```
    This ensures that the `EvoDHW` entity becomes unavailable if DHW data is not part of the latest successful update from the coordinator. If `self.coordinator.tcs.hotwater` becomes `None` (because DHW data was missing), this comparison will correctly result in `False`.

These changes will ensure that individual entities accurately reflect their availability based not only on the overall coordinator status but also on the presence of their specific data in the latest update, aligning with the `entity-unavailable` rule.

---

_Created at 2025-05-29 12:44:10. Prompt tokens: 22072, Output tokens: 1618, Total tokens: 31128._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
