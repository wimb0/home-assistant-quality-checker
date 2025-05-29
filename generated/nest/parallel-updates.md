# nest: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `parallel-updates` rule requires integrations to explicitly specify the `PARALLEL_UPDATES` constant in their entity platform files (e.g., `sensor.py`, `camera.py`). This constant controls how many entities of that platform can have their `async_update` method or service call handlers executed concurrently by Home Assistant.

This rule applies to the `nest` integration because it defines entities across multiple platforms: `camera`, `climate`, `event`, and `sensor`, as specified in `homeassistant/components/nest/__init__.py`:
```python
# homeassistant/components/nest/__init__.py
PLATFORMS = [Platform.CAMERA, Platform.CLIMATE, Platform.EVENT, Platform.SENSOR]
```

The `nest` integration utilizes a coordinator-like pattern for data updates. The `GoogleNestSubscriber` and `DeviceManager` (initialized in `async_setup_entry` in `__init__.py`) manage device data and push updates to entities. Entities subscribe to these updates using callbacks like `self._device.add_update_listener(self.async_write_ha_state)` or `self._device.add_event_callback(self._async_handle_event)`. This centralized update mechanism is relevant to the `parallel-updates` rule, as it often allows `PARALLEL_UPDATES = 0` for read-only platforms.

A review of the entity platform files reveals that none of them define the `PARALLEL_UPDATES` constant:
*   `homeassistant/components/nest/camera.py`: The `NestCameraBaseEntity` and its subclasses do not define `PARALLEL_UPDATES`.
*   `homeassistant/components/nest/climate.py`: The `ThermostatEntity` does not define `PARALLEL_UPDATES`.
*   `homeassistant/components/nest/event.py`: The `NestTraitEventEntity` does not define `PARALLEL_UPDATES`.
*   `homeassistant/components/nest/sensor.py`: The `SensorBase` and its subclasses do not define `PARALLEL_UPDATES`.

Since `PARALLEL_UPDATES` is not defined in any of these platform files, the integration does not follow the rule.

## Suggestions

To comply with the `parallel-updates` rule, the `PARALLEL_UPDATES` constant should be added to each relevant entity platform file. Given that the `nest` integration uses a coordinator pattern for state updates:

1.  **For `sensor.py` (read-only platform):**
    Add `PARALLEL_UPDATES = 0` at the top of `homeassistant/components/nest/sensor.py`.
    ```python
    # homeassistant/components/nest/sensor.py
    from __future__ import annotations

    import logging

    from google_nest_sdm.device import Device
    # ... other imports

    PARALLEL_UPDATES = 0  # Add this line

    _LOGGER = logging.getLogger(__name__)
    # ... rest of the file
    ```
    **Reasoning:** Sensors are read-only, and their state updates are managed by the central device manager. `PARALLEL_UPDATES = 0` indicates that Home Assistant's entity update scheduler does not need to limit concurrent `async_update` calls for these sensors (as updates are pushed).

2.  **For `event.py` (read-only platform):**
    Add `PARALLEL_UPDATES = 0` at the top of `homeassistant/components/nest/event.py`.
    ```python
    # homeassistant/components/nest/event.py
    from dataclasses import dataclass
    import logging
    # ... other imports

    PARALLEL_UPDATES = 0  # Add this line

    _LOGGER = logging.getLogger(__name__)
    # ... rest of the file
    ```
    **Reasoning:** The `event` platform is considered read-only for state updates in the context of this rule, and updates are pushed. `PARALLEL_UPDATES = 0` is appropriate.

3.  **For `camera.py` (platform with actions):**
    Add `PARALLEL_UPDATES = 0` at the top of `homeassistant/components/nest/camera.py`.
    ```python
    # homeassistant/components/nest/camera.py
    from __future__ import annotations

    from abc import ABC
    # ... other imports

    PARALLEL_UPDATES = 0  # Add this line

    _LOGGER = logging.getLogger(__name__)
    # ... rest of the file
    ```
    **Reasoning:** While cameras have actions (e.g., starting a stream), their state updates are coordinated. Setting `PARALLEL_UPDATES = 0` explicitly means Home Assistant will not impose an additional platform-specific limit on concurrent action calls (service calls). If the Nest API has specific strict limitations on concurrent commands, `PARALLEL_UPDATES = 1` could be considered, but `0` is a common choice when a coordinator handles state and no other specific platform limit is desired for actions.

4.  **For `climate.py` (platform with actions):**
    Add `PARALLEL_UPDATES = 0` at the top of `homeassistant/components/nest/climate.py`.
    ```python
    # homeassistant/components/nest/climate.py
    from __future__ import annotations

    from typing import Any, cast
    # ... other imports

    PARALLEL_UPDATES = 0  # Add this line

    # ... rest of the file
    ```
    **Reasoning:** Similar to cameras, climate entities have actions (e.g., setting temperature, mode). State updates are coordinated. `PARALLEL_UPDATES = 0` allows Home Assistant to manage concurrency for action calls without an additional platform-specific limit. If API limitations are a concern, `1` could be an alternative.

By adding `PARALLEL_UPDATES` to these files, the integration will explicitly declare its concurrency handling strategy for entity updates and actions, thereby satisfying the rule.

_Created at 2025-05-28 22:59:58. Prompt tokens: 32320, Output tokens: 1461, Total tokens: 36804_
