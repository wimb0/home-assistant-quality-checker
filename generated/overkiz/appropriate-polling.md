# overkiz: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **todo**                                                                 |

## Overview

The `appropriate-polling` rule applies to the `overkiz` integration because its `manifest.json` declares `iot_class: "local_polling"` (and it also supports cloud polling), and it utilizes a `DataUpdateCoordinator` to manage data fetching, which is one of the mechanisms for setting polling intervals.

The integration generally attempts to set appropriate polling intervals based on conditions:
*   The default polling interval for cloud connections is 30 seconds (`UPDATE_INTERVAL` in `const.py`), which is a common default for cloud-based event fetching.
*   When all devices are determined to be "stateless" (e.g., RTS-only devices that don't report their state back), the interval is changed to 60 minutes (`UPDATE_INTERVAL_ALL_ASSUMED_STATE`). This is an excellent choice, as frequent polling of stateless devices offers little benefit.
*   For local API connections, the interval is typically set to 5 seconds (`UPDATE_INTERVAL_LOCAL`).
*   The integration also intelligently reduces the polling interval to 1 second temporarily when a command is sent to a non-stateless device, allowing for quicker feedback, and then reverts to the default. This is a good practice for responsiveness.

However, the integration does **not fully follow** the rule due to the interaction of how these intervals are set for local API connections with stateless devices.

In `homeassistant/components/overkiz/__init__.py`, within the `async_setup_entry` function, the logic is as follows:
1.  The `OverkizDataUpdateCoordinator` is initialized with a default interval (30 seconds).
2.  If `coordinator.is_stateless` is true, the interval is updated to `UPDATE_INTERVAL_ALL_ASSUMED_STATE` (60 minutes).
3.  Subsequently, **regardless** of the stateless check, if `api_type == APIType.LOCAL` is true, the interval is updated to `UPDATE_INTERVAL_LOCAL` (5 seconds).

```python
# homeassistant/components/overkiz/__init__.py
# ...
    if coordinator.is_stateless:
        LOGGER.debug(
            "All devices have an assumed state. Update interval has been reduced to: %s",
            UPDATE_INTERVAL_ALL_ASSUMED_STATE,
        )
        coordinator.set_update_interval(UPDATE_INTERVAL_ALL_ASSUMED_STATE)

    if api_type == APIType.LOCAL: # This 'if' is independent of the 'if coordinator.is_stateless'
        LOGGER.debug(
            "Devices connect via Local API. Update interval has been reduced to: %s",
            UPDATE_INTERVAL_LOCAL,
        )
        coordinator.set_update_interval(UPDATE_INTERVAL_LOCAL)
# ...
```

This means that if a user has a local API setup consisting entirely of stateless devices (e.g., RTS blinds), the polling interval will be 5 seconds, not the more appropriate 60 minutes. Polling stateless devices every 5 seconds, even on a local API, is generally not considered "appropriate" as these devices do not report state changes, and the primary benefit of polling would be for availability or other infrequent events. The 60-minute interval specifically designed for stateless devices should take precedence.

## Suggestions

To make the `overkiz` integration compliant with the `appropriate-polling` rule, the logic for setting the update interval in `homeassistant/components/overkiz/__init__.py` should be adjusted to prioritize the stateless condition.

1.  **Modify the conditional logic for interval setting**:
    Ensure that if `coordinator.is_stateless` is true, the `UPDATE_INTERVAL_ALL_ASSUMED_STATE` (60 minutes) is the final polling interval for the coordinator's default, regardless of whether the API is local or cloud. The local API's specific interval should only apply if the devices are not all stateless.

    **Current Logic Snippet (for context):**
    ```python
    # homeassistant/components/overkiz/__init__.py (in async_setup_entry)
    # ...
    if coordinator.is_stateless:
        LOGGER.debug(
            "All devices have an assumed state. Update interval has been reduced to: %s",
            UPDATE_INTERVAL_ALL_ASSUMED_STATE,
        )
        coordinator.set_update_interval(UPDATE_INTERVAL_ALL_ASSUMED_STATE)

    if api_type == APIType.LOCAL:
        LOGGER.debug(
            "Devices connect via Local API. Update interval has been reduced to: %s",
            UPDATE_INTERVAL_LOCAL,
        )
        coordinator.set_update_interval(UPDATE_INTERVAL_LOCAL)
    # ...
    ```

    **Suggested Code Change:**
    Change the second `if` to an `elif` to ensure the stateless check takes precedence:
    ```python
    # homeassistant/components/overkiz/__init__.py (in async_setup_entry)
    # ...
    if coordinator.is_stateless:
        LOGGER.debug(
            "All devices have an assumed state. Update interval has been set to: %s", # "set to" instead of "reduced to" for clarity
            UPDATE_INTERVAL_ALL_ASSUMED_STATE,
        )
        coordinator.set_update_interval(UPDATE_INTERVAL_ALL_ASSUMED_STATE)
    elif api_type == APIType.LOCAL: # Changed from 'if' to 'elif'
        LOGGER.debug(
            "Devices connect via Local API (and are not all stateless). Update interval has been set to: %s", # "set to" and clarification
            UPDATE_INTERVAL_LOCAL,
        )
        coordinator.set_update_interval(UPDATE_INTERVAL_LOCAL)
    # If neither stateless nor local, the default from coordinator initialization (30s for cloud) is used.
    # ...
    ```

2.  **Reasoning for the suggestion**:
    This change ensures that the 60-minute polling interval (`UPDATE_INTERVAL_ALL_ASSUMED_STATE`), which is highly appropriate for stateless devices, is respected even on local API setups. Stateless devices do not report their state back, so frequent polling (even for device events like availability) is generally unnecessary and can put undue load on the local hub. The 5-second local polling interval (`UPDATE_INTERVAL_LOCAL`) would then correctly apply only to local API setups that include stateful devices. This aligns better with the rule's intent of setting a polling interval that "will serve the majority of users" by being responsible with polling frequency based on device characteristics.

_Created at 2025-05-28 12:08:45. Prompt tokens: 87153, Output tokens: 1581, Total tokens: 94655_
