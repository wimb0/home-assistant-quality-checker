# evohome: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule states that common patterns like data update coordinators and base entities should be placed in `coordinator.py` and `entity.py` respectively, to improve consistency and code organization.

This rule applies to the `evohome` integration as it utilizes both a data update coordinator and base entities.

The integration correctly follows this rule:

1.  **Coordinator:**
    *   The `evohome` integration uses a data update coordinator named `EvoDataUpdateCoordinator`.
    *   This coordinator is defined in the file `homeassistant/components/evohome/coordinator.py`, as shown in the provided code:
        ```python
        # homeassistant/components/evohome/coordinator.py
        class EvoDataUpdateCoordinator(DataUpdateCoordinator):
            """Coordinator for evohome integration/client."""
            # ...
        ```
    *   It is imported and instantiated in `homeassistant/components/evohome/__init__.py`:
        ```python
        # homeassistant/components/evohome/__init__.py
        from .coordinator import EvoDataUpdateCoordinator
        # ...
        async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
            """Load the Evohome config entry."""
            coordinator = EvoDataUpdateCoordinator(
                hass, _LOGGER, config_entry=config_entry, name=f"{DOMAIN}_coordinator"
            )
            # ...
        ```

2.  **Base Entity:**
    *   The integration defines base entities `EvoEntity` and `EvoChild` to reduce code duplication for its climate and water heater entities.
    *   These base entities are defined in the file `homeassistant/components/evohome/entity.py`:
        ```python
        # homeassistant/components/evohome/entity.py
        class EvoEntity(CoordinatorEntity[EvoDataUpdateCoordinator]):
            """Base for any evohome-compatible entity (controller, DHW, zone)."""
            # ...

        class EvoChild(EvoEntity):
            """Base for any evohome-compatible child entity (DHW, zone)."""
            # ...
        ```
    *   These base entities are then used by platform-specific entities, for example, in `homeassistant/components/evohome/climate.py`:
        ```python
        # homeassistant/components/evohome/climate.py
        from .entity import EvoChild, EvoEntity
        # ...
        class EvoClimateEntity(EvoEntity, ClimateEntity):
            # ...
        class EvoZone(EvoChild, EvoClimateEntity):
            # ...
        class EvoController(EvoClimateEntity): # Inherits from EvoClimateEntity which inherits from EvoEntity
            # ...
        ```
    *   And in `homeassistant/components/evohome/water_heater.py`:
        ```python
        # homeassistant/components/evohome/water_heater.py
        from .entity import EvoChild
        # ...
        class EvoDHW(EvoChild, WaterHeaterEntity):
            # ...
        ```

The integration adheres to the specified file naming and structure for common modules.

## Suggestions

No suggestions needed.

---

_Created at 2025-05-29 11:42:03. Prompt tokens: 21744, Output tokens: 837, Total tokens: 23183._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
