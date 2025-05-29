# evohome: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `entity-unique-id` rule requires that all entities provided by an integration have a unique ID. This ID must be unique per integration domain and per platform domain, allowing Home Assistant to track and manage entities consistently, enabling user customizations.

The `evohome` integration creates entities for `climate` (controllers and zones) and `water_heater` (DHW controllers). The rule applies to this integration.

The integration correctly assigns unique IDs to its entities:

1.  **Controller Entities (`EvoController` in `climate.py`):**
    The `EvoController` class, which represents the main Evohome controller, sets its unique ID using the controller's ID from the `evohomeasync2` library.
    ```python
    # homeassistant/components/evohome/climate.py
    class EvoController(EvoClimateEntity):
        # ...
        def __init__(
            self, coordinator: EvoDataUpdateCoordinator, evo_device: evo.ControlSystem
        ) -> None:
            # ...
            self._attr_unique_id = evo_device.id
            # ...
    ```
    This assigns the `id` of the `evo.ControlSystem` object as the unique ID for the controller's climate entity.

2.  **Zone Entities (`EvoZone` in `climate.py`):**
    The `EvoZone` class, representing individual heating zones, also sets a unique ID. It includes special handling for cases where a zone's ID might be identical to the controller's ID, ensuring uniqueness within the climate platform by appending a "z".
    ```python
    # homeassistant/components/evohome/climate.py
    class EvoZone(EvoChild, EvoClimateEntity):
        # ...
        def __init__(
            self, coordinator: EvoDataUpdateCoordinator, evo_device: evo.Zone
        ) -> None:
            # ...
            if evo_device.id == evo_device.tcs.id:
                # this system does not have a distinct ID for the zone
                self._attr_unique_id = f"{evo_device.id}z"
            else:
                self._attr_unique_id = evo_device.id
            # ...
    ```
    This ensures that each zone climate entity has a unique ID, derived from `evo_device.id` (the zone's ID), and is differentiated from the controller entity even if their base IDs from the API are the same.

3.  **DHW Entities (`EvoDHW` in `water_heater.py`):**
    The `EvoDHW` class, for domestic hot water controllers, sets its unique ID using the DHW device's ID.
    ```python
    # homeassistant/components/evohome/water_heater.py
    class EvoDHW(EvoChild, WaterHeaterEntity):
        # ...
        def __init__(
            self, coordinator: EvoDataUpdateCoordinator, evo_device: evo.HotWater
        ) -> None:
            # ...
            self._attr_unique_id = evo_device.id
            # ...
    ```
    This assigns the `id` of the `evo.HotWater` object as the unique ID for the DHW water_heater entity.

In all cases, `_attr_unique_id` is set using device-specific identifiers obtained from the `evohomeasync2` library. Assuming these library-provided IDs (`evo_device.id`) are unique for each physical or logical device (controller, zone, DHW unit) within a user's Evohome system, and stable across restarts, the integration meets the requirements of the `entity-unique-id` rule. The special handling in `EvoZone` further ensures uniqueness within the `climate` platform for the `evohome` integration.

## Suggestions

No suggestions needed.

---

_Created at 2025-05-29 11:44:10. Prompt tokens: 21732, Output tokens: 983, Total tokens: 25673._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
