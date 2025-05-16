# linkplay: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates)                                                     |
| Status | **todo**                                                                 |

## Overview

The `parallel-updates` rule requires that integrations explicitly specify the number of parallel updates allowed for their entity platforms. This is done by defining a module-level constant `PARALLEL_UPDATES` in each entity platform file (e.g., `sensor.py`, `light.py`). This constant helps manage the load on devices or services that may not handle many concurrent requests well, applying to both entity state updates and action calls.

This rule applies to the `linkplay` integration as it provides entities through the `button` and `media_player` platforms, as defined in `const.py`:
```python
PLATFORMS = [Platform.BUTTON, Platform.MEDIA_PLAYER]
```

The integration's compliance is as follows:

1.  **`media_player.py`**: This platform **correctly implements** the rule.
    It defines `PARALLEL_UPDATES = 1` at the module level:
    ```python
    # media_player.py
    ...
    SCAN_INTERVAL = timedelta(seconds=5)
    PARALLEL_UPDATES = 1 # Line 119


    async def async_setup_entry(
    ...
    ```
    This setting ensures that if multiple `linkplay` media player entities exist, their state updates (via `async_update`) will be performed sequentially, which is good practice for polled devices.

2.  **`button.py`**: This platform **does not currently implement** the rule.
    The file `button.py` is missing the `PARALLEL_UPDATES` constant. While button entities primarily handle actions (`async_press`) rather than continuous state updates, the rule explicitly states that `PARALLEL_UPDATES` applies to "both entity updates and actions calls." Therefore, it should be defined to control the concurrency of actions if multiple button entities from this platform are triggered simultaneously.

Since one of the entity platforms (`button.py`) does not specify `PARALLEL_UPDATES`, the integration does not fully follow the rule.

The integration does not use a central `DataUpdateCoordinator` for its entities; instead, each `LinkPlayMediaPlayerEntity` polls its associated `LinkPlayBridge` individually. Button entities also interact directly with their `LinkPlayBridge` upon action. Thus, the standard application of `PARALLEL_UPDATES` in each platform module is the appropriate way to manage request concurrency.

## Suggestions

To make the `linkplay` integration compliant with the `parallel-updates` rule, the `PARALLEL_UPDATES` constant should be added to the `button.py` file.

1.  **Modify `button.py`:**
    Add the following line at the top of the `button.py` file, typically near other constants or imports:

    ```python
    # button.py
    """Support for LinkPlay buttons."""

    from __future__ import annotations

    from collections.abc import Callable, Coroutine
    from dataclasses import dataclass
    import logging
    from typing import Any

    from linkplay.bridge import LinkPlayBridge

    from homeassistant.components.button import (
        ButtonDeviceClass,
        ButtonEntity,
        ButtonEntityDescription,
    )
    from homeassistant.const import EntityCategory
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from . import LinkPlayConfigEntry
    from .entity import LinkPlayBaseEntity, exception_wrap

    _LOGGER = logging.getLogger(__name__)

    PARALLEL_UPDATES = 1  # <--- Add this line
    ```

**Reasoning for the suggestion:**
*   Adding `PARALLEL_UPDATES = 1` to `button.py` will ensure that if multiple `linkplay` button actions (e.g., "Sync time" or "Restart" across several devices, or different buttons on the same device) are triggered concurrently (perhaps via automations), Home Assistant will process these `async_press` calls sequentially for this platform. This helps prevent overwhelming the devices with too many commands at once, aligning with the rule's intent.
*   A value of `1` is a safe default for action-oriented entities, especially for operations like "restart" or "timesync" which might be sensitive to concurrent execution on the device. If it's known that LinkPlay devices can safely handle concurrent actions without issues, `0` (unlimited, or rather, limited by HA's global defaults) could be considered, but `1` is generally preferred unless specific knowledge justifies otherwise.

By making this change, the `linkplay` integration will fully comply with the `parallel-updates` rule, as all its entity platforms will have an explicit definition for parallel request handling.

_Created at 2025-05-11 15:02:04. Prompt tokens: 10603, Output tokens: 1139, Total tokens: 14297_
