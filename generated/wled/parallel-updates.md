# wled: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `parallel-updates` rule requires integrations to explicitly specify the number of parallel updates allowed for each entity platform. This is important for devices or services that may not handle a large number of concurrent requests well. When a `DataUpdateCoordinator` is used, read-only platforms (like `sensor`) can typically set `PARALLEL_UPDATES = 0` as data fetching is centralized. Platforms with actions (like `light`, `switch`, `button`, `update`) should set an appropriate limit, often `1`, to serialize actions to the device.

The `wled` integration uses a `WLEDDataUpdateCoordinator` for its entities. The rule applies because it provides entities across multiple platforms.

The integration partially follows this rule:
*   **`light.py`**: Correctly defines `PARALLEL_UPDATES = 1`. This is appropriate as light entities perform actions (e.g., turn on/off, change color) that involve sending commands to the WLED device.
*   **`number.py`**: Correctly defines `PARALLEL_UPDATES = 1`. Number entities (e.g., speed, intensity) perform actions.
*   **`select.py`**: Correctly defines `PARALLEL_UPDATES = 1`. Select entities (e.g., preset, playlist) perform actions.
*   **`switch.py`**: Correctly defines `PARALLEL_UPDATES = 1`. Switch entities perform actions.

However, the following platform files are missing the `PARALLEL_UPDATES` constant:

*   **`sensor.py`**: This file sets up `WLEDSensorEntity` instances, which are read-only and derive from `CoordinatorEntity`. According to the rule, for coordinator-based read-only platforms, `PARALLEL_UPDATES = 0` should be specified.
*   **`update.py`**: This file sets up `WLEDUpdateEntity`. The `UpdateEntity` class has an action method (`async_install`). `PARALLEL_UPDATES` should be explicitly defined, likely to `1`, to ensure firmware updates are processed sequentially if multiple WLED devices are updated.
*   **`button.py`**: This file sets up `WLEDRestartButton`. The `ButtonEntity` class has an action method (`async_press`). `PARALLEL_UPDATES` should be explicitly defined, likely to `1`, to serialize restart commands.

Because `PARALLEL_UPDATES` is not specified in all applicable platform files, the integration does not fully comply with the rule.

## Suggestions

To comply with the `parallel-updates` rule, the following changes are recommended:

1.  **In `sensor.py`:**
    Add `PARALLEL_UPDATES = 0` at the module level.
    ```python
    # sensor.py
    from __future__ import annotations

    from collections.abc import Callable
    # ... other imports ...

    from .entity import WLEDEntity

    PARALLEL_UPDATES = 0  # Add this line

    @dataclass(frozen=True, kw_only=True)
    # ... rest of the file
    ```
    **Reasoning:** Sensor entities in this integration are read-only and use a `DataUpdateCoordinator`. The rule states that for such platforms, `PARALLEL_UPDATES = 0` is appropriate as the coordinator already centralizes data updates. This setting means Home Assistant won't limit parallel updates for these entities, which is fine as their state comes from the coordinator.

2.  **In `update.py`:**
    Add `PARALLEL_UPDATES = 1` (or another carefully considered value) at the module level.
    ```python
    # update.py
    from __future__ import annotations

    from typing import Any, cast

    from homeassistant.components.update import (
        # ...
    )
    # ... other imports ...
    from .helpers import wled_exception_handler

    PARALLEL_UPDATES = 1  # Add this line

    async def async_setup_entry(
    # ... rest of the file
    ```
    **Reasoning:** The `WLEDUpdateEntity` performs an action (`async_install`). Setting `PARALLEL_UPDATES = 1` ensures that if multiple WLED devices are being updated simultaneously via Home Assistant, the install commands are sent one at a time from the `update` platform, preventing potential issues with overwhelming the devices or the network with firmware update requests.

3.  **In `button.py`:**
    Add `PARALLEL_UPDATES = 1` (or another carefully considered value) at the module level.
    ```python
    # button.py
    from __future__ import annotations

    from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
    # ... other imports ...
    from .helpers import wled_exception_handler

    PARALLEL_UPDATES = 1  # Add this line

    async def async_setup_entry(
    # ... rest of the file
    ```
    **Reasoning:** The `WLEDRestartButton` performs an action (`async_press`). Setting `PARALLEL_UPDATES = 1` ensures that restart commands for multiple WLED devices are processed sequentially by Home Assistant's button platform, which is generally safer for device operations.

By explicitly setting `PARALLEL_UPDATES` in these files, the integration will fully adhere to the rule, improving robustness and predictability when interacting with WLED devices.

_Created at 2025-05-10 22:56:30. Prompt tokens: 21218, Output tokens: 1330, Total tokens: 25442_
