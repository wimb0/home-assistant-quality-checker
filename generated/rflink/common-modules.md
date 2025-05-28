# rflink: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [rflink](https://www.home-assistant.io/integrations/rflink/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule mandates that common architectural patterns within Home Assistant integrations be placed in standardized filenames to improve consistency and discoverability. Specifically, it requires:
1.  Data fetching coordinators (typically using `DataUpdateCoordinator`) to be placed in `coordinator.py`.
2.  Base entity classes, used to reduce code duplication across an integration's platforms, to be placed in `entity.py`.

The `rflink` integration is assessed against these two requirements:

**1. Base Entities (`entity.py`):**
The `rflink` integration defines several base entity classes to share common functionality and properties among its various entity platforms (binary_sensor, cover, light, sensor, switch). These base classes include:
*   `RflinkDevice`: Found in `homeassistant/components/rflink/entity.py`, this class serves as the fundamental base for RFLink entities.
*   `RflinkCommand`: Also in `entity.py`, this class inherits from `RflinkDevice` and adds methods for sending commands to RFLink devices.
*   `SwitchableRflinkDevice`: Defined in `entity.py`, this class inherits from `RflinkCommand` and provides common logic for entities that can be turned on or off, like lights and switches.

These base classes are correctly located in `homeassistant/components/rflink/entity.py`. For instance:
*   `homeassistant/components/rflink/light.py` uses `SwitchableRflinkDevice` as a base for `RflinkLight`.
*   `homeassistant/components/rflink/switch.py` uses `SwitchableRflinkDevice` for `RflinkSwitch`.
*   `homeassistant/components/rflink/sensor.py` uses `RflinkDevice` for `RflinkSensor`.
*   `homeassistant/components/rflink/binary_sensor.py` uses `RflinkDevice` for `RflinkBinarySensor`.
*   `homeassistant/components/rflink/cover.py` uses `RflinkCommand` for `RflinkCover`.

This demonstrates that the `rflink` integration fully complies with the rule's requirement for placing base entities in an `entity.py` file.

**2. Coordinators for Data Fetching (`coordinator.py`):**
The rule specifies that coordinators, particularly those derived from `DataUpdateCoordinator` used for centralizing data fetching, should reside in a `coordinator.py` file.

The `rflink` integration's architecture is event-driven. It establishes a connection to an RFLink gateway (serial or TCP) and listens for incoming messages. The core connection management and event dispatching logic are handled in `homeassistant/components/rflink/__init__.py`. When data is received from the RFLink gateway, an `event_callback` processes it and dispatches it to the relevant entities.

This design does not use the `DataUpdateCoordinator` pattern, which is typically employed for integrations that periodically poll an external API or device for state updates. Since `rflink` receives data pushed from the gateway rather than fetching it on a schedule, it does not have a "data fetching coordinator" in the sense described by the rule and its examples.

Consequently, the requirement to place a data fetching coordinator in `coordinator.py` is not directly applicable in a way that would constitute a violation. The integration does not use this specific pattern, so there is no misplaced coordinator of this type.

**Conclusion:**
The `rflink` integration correctly follows the applicable aspects of the `common-modules` rule. It properly places its base entity classes in `entity.py`. The part of the rule concerning the placement of data fetching coordinators in `coordinator.py` is not violated because the integration does not use that specific architectural pattern.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 13:25:02. Prompt tokens: 17655, Output tokens: 926, Total tokens: 22889_
