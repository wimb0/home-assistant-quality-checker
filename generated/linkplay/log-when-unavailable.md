# linkplay: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `log-when-unavailable` rule requires that an integration logs a message at `INFO` level when a connected device or service becomes unavailable, and again when it becomes available. This logging should only occur once for each state transition to avoid spamming the logs.

This rule applies to the `linkplay` integration as it communicates with network-based LinkPlay devices that can become unreachable. The integration uses an `async_update` method within its `LinkPlayMediaPlayerEntity` to poll the device status.

Currently, the `linkplay` integration does not fully follow this rule:

1.  **No `INFO` log when unavailable:** When a LinkPlay device becomes unavailable (after `RETRY_POLL_MAXIMUM` failed updates), `LinkPlayMediaPlayerEntity` sets `self._attr_available = False` in `media_player.py`. However, it does not log an `INFO` message indicating that the device is now unavailable. The existing `exception_wrap` decorator might log an `ERROR` if `HomeAssistantError` is raised, but this is not the specific `INFO` level log required by the rule, nor is it tied to the "once per unavailable period" logic. In the current `async_update`'s `except LinkPlayRequestException` block, the exception is handled locally (by incrementing `_retry_count` and potentially setting `_attr_available = False`), so `exception_wrap` does not raise a `HomeAssistantError` from this path.
2.  **No `INFO` log when back online:** When a device becomes available again after a period of unavailability, there is no `INFO` message logged to indicate this state change.
3.  **No flag to log once:** There is no mechanism (e.g., an instance variable like `_unavailable_logged`) to ensure that the unavailability/availability messages are logged only once per state transition.

The `LinkPlayMediaPlayerEntity` in `media_player.py` handles device polling and availability. This is where the logging logic should be implemented.

## Suggestions

To make the `linkplay` integration compliant with the `log-when-unavailable` rule, modify the `LinkPlayMediaPlayerEntity` class in `media_player.py` as follows:

1.  **Add an `_unavailable_logged` flag:**
    Initialize a boolean instance variable `self._unavailable_logged = False` in the `__init__` method. This flag will track whether the "unavailable" state has been logged for the current period of unavailability.

2.  **Update the `async_update` method:**
    Modify the `async_update` method to include logging logic based on the state transitions and the `_unavailable_logged` flag.

```python
# media_player.py
import logging # Ensure logging is imported
# ... other imports ...

_LOGGER = logging.getLogger(__name__) # Define logger for the module

# ...

class LinkPlayMediaPlayerEntity(LinkPlayBaseEntity, MediaPlayerEntity):
    """Representation of a LinkPlay media player."""

    # ... (existing attributes) ...
    _unavailable_logged: bool # Add type hint for the new attribute

    def __init__(self, bridge: LinkPlayBridge) -> None:
        """Initialize the LinkPlay media player."""
        super().__init__(bridge)
        self._attr_unique_id = bridge.device.uuid
        self._retry_count = 0
        self._unavailable_logged = False # Initialize the flag

        self._attr_source_list = [
            SOURCE_MAP[playing_mode] for playing_mode in bridge.device.playmode_support
        ]
        self._attr_sound_mode_list = [
            mode.value for mode in bridge.player.available_equalizer_modes
        ]

    @exception_wrap # This decorator can be kept as is
    async def async_update(self) -> None:
        """Update the state of the media player."""
        try:
            await self._bridge.player.update_status()
        except LinkPlayRequestException as ex:
            self._retry_count += 1
            if self._retry_count >= RETRY_POLL_MAXIMUM:
                # Device is considered unavailable after RETRY_POLL_MAXIMUM failures
                if self._attr_available or not self._unavailable_logged: # Log if previously available or first time logging this unavailability
                    # Ensure self._attr_available is False before checking _unavailable_logged to correctly log transition to False
                    # More precisely, we log if we haven't logged for *this specific* unavailability period.
                    # The `self._attr_available` check handles the transition from available to unavailable.
                    # The `not self._unavailable_logged` handles logging only once.
                    if not self._unavailable_logged:
                        _LOGGER.info(
                            "LinkPlay device %s (%s) is unavailable after %s retries: %s",
                            self._bridge.device.name,
                            self._bridge.host,
                            RETRY_POLL_MAXIMUM,
                            ex,
                        )
                        self._unavailable_logged = True
                self._attr_available = False # Mark entity as unavailable
            # If retry_count < RETRY_POLL_MAXIMUM, the entity remains in its current _attr_available state.
            # No specific "unavailable" log according to this rule is generated yet.
        else:
            # Update was successful
            
            # If it was previously logged as unavailable, log that it's back online
            if self._unavailable_logged:
                _LOGGER.info(
                    "LinkPlay device %s (%s) is back online",
                    self._bridge.device.name,
                    self._bridge.host,
                )
                self._unavailable_logged = False # Reset flag
            
            # In all success cases (recovered or was never unavailable according to log):
            self._retry_count = 0
            # _update_properties() will set self._attr_available = True and update other states
            self._update_properties()

    def _update_properties(self) -> None:
        """Update the properties of the media player."""
        self._attr_available = True # This is called on successful update
        self._attr_state = STATE_MAP[self._bridge.player.status]
        # ... (rest of the method remains the same) ...

    # ... (rest of the class methods) ...
```

**Explanation of Changes:**

*   **`_unavailable_logged` flag:** This new boolean instance variable tracks if an "unavailable" message has been logged for the current continuous period of unavailability. It is initialized to `False`.
*   **In the `except LinkPlayRequestException` block (when an update fails):**
    *   If `self._retry_count` reaches `RETRY_POLL_MAXIMUM`:
        *   It checks if `self._unavailable_logged` is `False`. If so, it means this is the first time (for this period of unavailability) that the device is confirmed unavailable.
        *   An `INFO` message is logged stating the device name, host, retry count, and the exception.
        *   `self._unavailable_logged` is set to `True` to prevent further "unavailable" logs for this period.
        *   `self._attr_available` is set to `False`.
*   **In the `else` block (when an update is successful):**
    *   It checks if `self._unavailable_logged` is `True`. If so, it means the device was previously logged as unavailable and is now back online.
    *   An `INFO` message is logged stating the device name and host are back online.
    *   `self._unavailable_logged` is set to `False`.
    *   `self._retry_count` is reset, and `self._update_properties()` is called (which sets `self._attr_available = True` and refreshes other entity states).

These changes implement the required logging behavior as specified by the `log-when-unavailable` rule for entities using `async_update`.

_Created at 2025-05-11 15:01:24. Prompt tokens: 11891, Output tokens: 1923, Total tokens: 22521_
