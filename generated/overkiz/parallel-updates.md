# overkiz: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `parallel-updates` rule requires that integrations explicitly specify the number of parallel updates allowed for their entities. This is important for devices or services that may not handle a large number of concurrent requests well. The `PARALLEL_UPDATES` constant should be defined at the module level in each platform file (e.g., `sensor.py`, `switch.py`). When a `DataUpdateCoordinator` is used, read-only platforms (like `binary_sensor`, `sensor`) should set `PARALLEL_UPDATES = 0`. For platforms involving actions, an appropriate limit (e.g., `1`) should be set to manage concurrency for action calls.

This rule applies to the `overkiz` integration because it provides entities across multiple platforms, many of which involve sending commands (actions) to devices via the Overkiz API. The integration uses a `OverkizDataUpdateCoordinator` for managing data updates.

The `overkiz` integration currently does **NOT** follow this rule. None of its platform files define the `PARALLEL_UPDATES` constant.
Specifically, the following platform files are missing this constant:
- `homeassistant/components/overkiz/alarm_control_panel.py`
- `homeassistant/components/overkiz/binary_sensor.py`
- `homeassistant/components/overkiz/button.py`
- `homeassistant/components/overkiz/climate/__init__.py`
- `homeassistant/components/overkiz/cover/__init__.py`
- `homeassistant/components/overkiz/light.py`
- `homeassistant/components/overkiz/lock.py`
- `homeassistant/components/overkiz/number.py`
- `homeassistant/components/overkiz/scene.py`
- `homeassistant/components/overkiz/select.py`
- `homeassistant/components/overkiz/sensor.py`
- `homeassistant/components/overkiz/siren.py`
- `homeassistant/components/overkiz/switch.py`
- `homeassistant/components/overkiz/water_heater/__init__.py`

Without `PARALLEL_UPDATES` being set, Home Assistant's default behavior is to update/call actions on all entities of a platform in parallel, which could potentially overwhelm the Overkiz API or hub, especially since the `pyoverkiz` library handles exceptions like `TooManyRequestsException` and `TooManyConcurrentRequestsException`, indicating API sensitivity.

## Suggestions

To make the `overkiz` integration compliant with the `parallel-updates` rule, the `PARALLEL_UPDATES` constant should be explicitly defined in each platform's main Python file.

1.  **For read-only platforms (updated via the coordinator):**
    These platforms primarily display data fetched by the `OverkizDataUpdateCoordinator`. Entity updates are already centralized. Setting `PARALLEL_UPDATES = 0` disables Home Assistant's per-platform update throttling for these, which is appropriate as the coordinator handles updates.

    *   In `homeassistant/components/overkiz/binary_sensor.py`:
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 0

        # ... rest of the file
        from homeassistant.components.binary_sensor import (
            BinarySensorDeviceClass,
        # ...
        ```

    *   In `homeassistant/components/overkiz/sensor.py`:
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 0

        # ... rest of the file
        from homeassistant.components.sensor import (
            SensorDeviceClass,
        # ...
        ```

2.  **For platforms with actions:**
    These platforms allow users to send commands to devices (e.g., turn on a switch, open a cover). The `PARALLEL_UPDATES` setting will control how many such actions Home Assistant attempts to send concurrently for entities within that platform. Given that the Overkiz API can raise `TooManyRequestsException`, a conservative limit is advisable. `PARALLEL_UPDATES = 1` is a common safe choice, meaning actions for entities of that platform will be processed one at a time by Home Assistant. The integration maintainer might decide on a slightly higher value if the API and `pyoverkiz` library can reliably handle more, or `0` if `pyoverkiz` provides sufficient internal queueing/rate-limiting for outgoing commands.

    The following files should have `PARALLEL_UPDATES = 1` (or another suitable limit) added at the module level:

    *   `homeassistant/components/overkiz/alarm_control_panel.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        from __future__ import annotations
        # ...
        ```
    *   `homeassistant/components/overkiz/button.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        from __future__ import annotations
        # ...
        ```
    *   `homeassistant/components/overkiz/climate/__init__.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        """Climate entities for the Overkiz (by Somfy) integration."""
        # ...
        ```
    *   `homeassistant/components/overkiz/cover/__init__.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        """Support for Overkiz covers - shutters etc."""
        # ...
        ```
    *   `homeassistant/components/overkiz/light.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        from __future__ import annotations
        # ...
        ```
    *   `homeassistant/components/overkiz/lock.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        from __future__ import annotations
        # ...
        ```
    *   `homeassistant/components/overkiz/number.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        from __future__ import annotations
        # ...
        ```
    *   `homeassistant/components/overkiz/scene.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        from __future__ import annotations
        # ...
        ```
    *   `homeassistant/components/overkiz/select.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        from __future__ import annotations
        # ...
        ```
    *   `homeassistant/components/overkiz/siren.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        from typing import Any
        # ...
        ```
    *   `homeassistant/components/overkiz/switch.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        from __future__ import annotations
        # ...
        ```
    *   `homeassistant/components/overkiz/water_heater/__init__.py`
        ```python
        # Add this at the top of the file
        PARALLEL_UPDATES = 1

        # ... rest of the file
        """Support for Overkiz water heater devices."""
        # ...
        ```

**Why these changes satisfy the rule:**
By explicitly defining `PARALLEL_UPDATES` in each platform file, the integration will adhere to the best practice of managing request parallelism.
- For read-only platforms, `PARALLEL_UPDATES = 0` correctly reflects that data updates are centralized by the coordinator.
- For platforms with actions, `PARALLEL_UPDATES = 1` (or another chosen value) will utilize Home Assistant's built-in mechanism to limit concurrent action calls, helping to prevent overloading the Overkiz API and improving the reliability of command execution. This makes the integration's behavior predictable and robust in terms of API interaction.

_Created at 2025-05-28 12:23:42. Prompt tokens: 86960, Output tokens: 2130, Total tokens: 93568_
