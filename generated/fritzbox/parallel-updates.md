```markdown
# fritzbox: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `parallel-updates` rule requires integrations to specify the `PARALLEL_UPDATES` constant in each platform file (`binary_sensor.py`, `sensor.py`, `switch.py`, etc.). This constant limits the number of simultaneous update requests sent to a device or service, preventing overload.

This integration uses a `DataUpdateCoordinator` (`FritzboxDataUpdateCoordinator` defined in `coordinator.py`) to centralize the polling of data from the FRITZ!Box. The rule states that when a coordinator is used, read-only platforms can set `PARALLEL_UPDATES = 0` because the coordinator handles the data fetching frequency. However, the rule also applies to action calls made by entities (e.g., turning a switch on, setting a climate temperature). These actions are typically independent of the coordinator's polling cycle and might be executed in parallel if not explicitly limited.

Reviewing the provided code, the `PARALLEL_UPDATES` constant is missing from all platform files:

*   `homeassistant/components/fritzbox/binary_sensor.py` (Read-only platform)
*   `homeassistant/components/fritzbox/button.py` (Action platform)
*   `homeassistant/components/fritzbox/climate.py` (Action platform)
*   `homeassistant/components/fritzbox/cover.py` (Action platform)
*   `homeassistant/components/fritzbox/light.py` (Action platform)
*   `homeassistant/components/fritzbox/sensor.py` (Read-only platform)
*   `homeassistant/components/fritzbox/switch.py` (Action platform)

Although the coordinator manages the data updates efficiently, the actions (like `async_turn_on`, `async_set_temperature`, etc.) in files like `switch.py`, `climate.py`, `cover.py`, `light.py`, and `button.py` execute blocking calls via `hass.async_add_executor_job(self.data.set_...)`. If multiple action calls are triggered simultaneously by Home Assistant (e.g., via a script or automation turning on multiple switches), these blocking calls could potentially happen in parallel, potentially overwhelming the FRITZ!Box API. Setting `PARALLEL_UPDATES` on these platforms helps limit this parallelism for action execution.

Therefore, the integration does not fully follow the rule as the `PARALLEL_UPDATES` constant is not defined in any platform file.

## Suggestions

To comply with the `parallel-updates` rule, add the `PARALLEL_UPDATES` constant to the top of each platform file:

1.  For read-only platforms (`binary_sensor.py`, `sensor.py`): Since a `DataUpdateCoordinator` is used for data fetching, set `PARALLEL_UPDATES = 0`. This explicitly signals that platform-level update parallelism is not needed for state updates, as the coordinator handles the rate.

    ```python
    # homeassistant/components/fritzbox/binary_sensor.py
    from __future__ import annotations

    from collections.abc import Callable
    from dataclasses import dataclass
    from typing import Final

    from pyfritzhome.fritzhomedevice import FritzhomeDevice

    from homeassistant.components.binary_sensor import (
        BinarySensorDeviceClass,
        BinarySensorEntity,
        BinarySensorEntityDescription,
    )
    from homeassistant.const import EntityCategory
    from homeassistant.core import HomeAssistant, callback
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import FritzboxConfigEntry
    from .entity import FritzBoxDeviceEntity
    from .model import FritzEntityDescriptionMixinBase

    PARALLEL_UPDATES = 0 # Add this line

    # ... rest of the file
    ```
    Apply the same change to `homeassistant/components/fritzbox/sensor.py`.

2.  For platforms with actions (`button.py`, `climate.py`, `cover.py`, `light.py`, `switch.py`): Set `PARALLEL_UPDATES` to a small number, typically `1`, to limit how many action calls for entities on that specific platform can be executed concurrently. This prevents potentially overloading the FRITZ!Box API with simultaneous commands.

    ```python
    # homeassistant/components/fritzbox/switch.py
    from __future__ import annotations

    from typing import Any

    from homeassistant.components.switch import SwitchEntity
    from homeassistant.core import HomeAssistant, callback
    from homeassistant.exceptions import HomeAssistantError
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .const import DOMAIN
    from .coordinator import FritzboxConfigEntry
    from .entity import FritzBoxDeviceEntity

    PARALLEL_UPDATES = 1 # Add this line

    # ... rest of the file
    ```
    Apply the same change (with `PARALLEL_UPDATES = 1`) to `homeassistant/components/fritzbox/button.py`, `homeassistant/components/fritzbox/climate.py`, `homeassistant/components/fritzbox/cover.py`, and `homeassistant/components/fritzbox/light.py`.

These changes ensure that the integration respects the device's potential limitations regarding simultaneous requests for both state updates (handled by the coordinator) and action executions.
```

_Created at 2025-05-25 11:35:04. Prompt tokens: 18951, Output tokens: 1318, Total tokens: 21650_
