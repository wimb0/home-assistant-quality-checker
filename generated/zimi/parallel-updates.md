# zimi: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [zimi](https://www.home-assistant.io/integrations/zimi/) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `parallel-updates` rule requires integrations to explicitly specify the number of parallel updates (which includes action calls) that Home Assistant can make to devices or services. This is done by defining a `PARALLEL_UPDATES` constant at the module level in each entity platform file (e.g., `light.py`, `switch.py`, `fan.py`).

This rule applies to the `zimi` integration because it provides entities through several platforms: `fan`, `light`, and `switch`, all of which involve sending commands to the Zimi devices.

The `zimi` integration currently does **not** follow this rule. An examination of the platform files reveals the absence of the `PARALLEL_UPDATES` constant:
*   In `homeassistant/components/zimi/fan.py`, `PARALLEL_UPDATES` is not defined.
*   In `homeassistant/components/zimi/light.py`, `PARALLEL_UPDATES` is not defined.
*   In `homeassistant/components/zimi/switch.py`, `PARALLEL_UPDATES` is not defined.

While the `zimi` integration uses a push-based mechanism for state updates from devices (as indicated by `_attr_should_poll = False` in `entity.py` and the use of `_device.subscribe()` and `notify()`), the `PARALLEL_UPDATES` setting is still crucial for controlling the concurrency of action calls (e.g., `async_turn_on`, `async_turn_off`, `async_set_percentage`). Without this constant, Home Assistant will use its default concurrency, which might not be optimal for the Zimi controller or the underlying `zcc-helper` library, potentially leading to issues if too many commands are sent simultaneously.

The `quality_scale.yaml` file for the `zimi` integration also lists `parallel-updates` with a `status: todo` and a comment: "Test of parallel updates will be done before setting." This indicates awareness of the requirement.

## Suggestions

To comply with the `parallel-updates` rule, the `PARALLEL_UPDATES` constant should be explicitly defined in each relevant platform file.

1.  **Determine an appropriate value for `PARALLEL_UPDATES`:**
    The ideal value depends on how well the Zimi controller and the `zcc-helper` library handle concurrent requests.
    *   If the Zimi system is sensitive to multiple simultaneous commands, `PARALLEL_UPDATES = 1` is a safe choice, ensuring commands are sent sequentially for entities within that platform.
    *   If the Zimi system and `zcc-helper` can handle more concurrent requests, a slightly higher value might be appropriate.
    *   If the `zcc-helper` library or the Zimi controller itself has robust internal queuing and concurrency management for outgoing commands, and there's no risk of overwhelming the device, `PARALLEL_UPDATES = 0` (unlimited from Home Assistant's perspective) could be used. However, this should be chosen with care.
    The rule emphasizes *explicitly setting* the value.

2.  **Add `PARALLEL_UPDATES` to platform files:**

    **In `homeassistant/components/zimi/fan.py`:**
    Add the following line at the beginning of the file (e.g., after imports):
    ```python
    # homeassistant/components/zimi/fan.py
    # ... other imports ...

    PARALLEL_UPDATES = 1  # Or another determined appropriate value

    _LOGGER = logging.getLogger(__name__)
    # ... rest of the file ...
    ```

    **In `homeassistant/components/zimi/light.py`:**
    Add the following line at the beginning of the file:
    ```python
    # homeassistant/components/zimi/light.py
    # ... other imports ...

    PARALLEL_UPDATES = 1  # Or another determined appropriate value

    _LOGGER = logging.getLogger(__name__)
    # ... rest of the file ...
    ```

    **In `homeassistant/components/zimi/switch.py`:**
    Add the following line at the beginning of the file:
    ```python
    # homeassistant/components/zimi/switch.py
    # ... other imports ...

    PARALLEL_UPDATES = 1  # Or another determined appropriate value

    _LOGGER = logging.getLogger(__name__)
    # ... rest of the file ...
    ```

By adding `PARALLEL_UPDATES` to each platform file, the integration explicitly declares how Home Assistant should manage the concurrency of outgoing commands to Zimi devices for entities of that specific platform, thereby satisfying the rule. This allows for better control and stability, preventing potential issues from overwhelming the Zimi controller or devices.

_Created at 2025-05-14 14:52:18. Prompt tokens: 7633, Output tokens: 1178, Total tokens: 11335_
