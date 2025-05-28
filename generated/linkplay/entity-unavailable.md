# linkplay: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `entity-unavailable` rule requires that if an integration cannot fetch data from a device or service, it should mark the corresponding entity as unavailable. This provides a more accurate representation of the entity's state than showing stale data.

This rule applies to the `linkplay` integration, specifically to the `LinkPlayMediaPlayerEntity` defined in `media_player.py`. This entity polls the LinkPlay device for its status using an `async_update` method.

The `linkplay` integration currently does **not** fully follow this rule. Here's why:

1.  The `LinkPlayMediaPlayerEntity.async_update` method is decorated with `@exception_wrap` (defined in `entity.py`).
2.  Inside `async_update`, the primary data fetching call is `await self._bridge.player.update_status()`.
3.  If `_bridge.player.update_status()` fails and raises a `LinkPlayRequestException`, this exception is caught by the `@exception_wrap` decorator *before* it can be caught by the `try...except LinkPlayRequestException` block *within* the `async_update` method itself.
4.  The `exception_wrap` decorator then re-raises the `LinkPlayRequestException` as a generic `HomeAssistantError`.
5.  Consequently, the logic within `async_update`'s own `except LinkPlayRequestException:` block, which is intended to increment a `_retry_count` and eventually set `self._attr_available = False` if `self._retry_count >= RETRY_POLL_MAXIMUM`, is never executed.
    ```python
    # In media_player.py, LinkPlayMediaPlayerEntity
    @exception_wrap # This decorator intercepts LinkPlayRequestException
    async def async_update(self) -> None:
        """Update the state of the media player."""
        try:
            await self._bridge.player.update_status()
            self._retry_count = 0
            self._update_properties() # This sets self._attr_available = True
        except LinkPlayRequestException: # This block is effectively bypassed
            self._retry_count += 1
            if self._retry_count >= RETRY_POLL_MAXIMUM:
                self._attr_available = False # This line is not reached
    ```
6.  When Home Assistant core's entity update mechanism catches a generic `HomeAssistantError` (that is not `UpdateFailed` or `PlatformNotReady`) raised from `async_update`, it logs the error but does not automatically mark the entity as unavailable. The entity remains in its previous state (potentially `available` with stale data).

Therefore, if communication with the LinkPlay device fails persistently, the `LinkPlayMediaPlayerEntity` will not be marked as unavailable as required by the rule.

The `LinkPlayButton` entity does not poll for data using `async_update`, so its availability is less directly covered by the primary mechanism described in this rule's examples. Its availability typically relies on the device it's associated with or is static. The focus for this rule is on polling entities like `LinkPlayMediaPlayerEntity`.

## Suggestions

To make the `linkplay` integration compliant with the `entity-unavailable` rule for `LinkPlayMediaPlayerEntity`, the handling of exceptions during data fetching in `async_update` needs to be revised. The goal is to ensure `self._attr_available` is set to `False` when data cannot be fetched after a defined number of retries.

1.  **Remove `@exception_wrap` from `LinkPlayMediaPlayerEntity.async_update`**:
    This will allow the `async_update` method to handle `LinkPlayRequestException` directly. The `@exception_wrap` decorator can remain on other methods (like service call handlers, e.g., `async_set_volume_level`) where raising `HomeAssistantError` for command failures is appropriate.

2.  **Adjust the `try...except` block in `async_update`**:
    Ensure that `LinkPlayRequestException` is caught and handled to update `_retry_count` and `_attr_available`.
    *   If `_bridge.player.update_status()` succeeds: Reset `_retry_count` and call `_update_properties()` (which sets `self._attr_available = True`).
    *   If `LinkPlayRequestException` occurs: Increment `_retry_count`.
        *   If `_retry_count < RETRY_POLL_MAXIMUM`, the entity can remain available (logging the temporary error is advisable).
        *   If `_retry_count >= RETRY_POLL_MAXIMUM`, set `self._attr_available = False`.
    *   It's also good practice to include a broader `except Exception:` to catch any other unexpected errors during the update process and mark the entity unavailable to prevent unhandled exceptions from stopping updates.

Here's an example of how `media_player.py`'s `LinkPlayMediaPlayerEntity.async_update` could be modified:

```python
# In media_player.py

# Remove @exception_wrap from this method
async def async_update(self) -> None:
    """Update the state of the media player."""
    try:
        await self._bridge.player.update_status()

        # If the entity was previously unavailable or in a retry state,
        # and is now successful, reset retry count and log recovery.
        if not self.available or self._retry_count > 0:
            _LOGGER.info(
                "Communication with LinkPlay device %s restored",
                self._bridge.device.name or self.entity_id,
            )
        
        self._retry_count = 0
        # _update_properties() correctly sets self._attr_available = True
        # and updates other entity states.
        self._update_properties()

    except LinkPlayRequestException as err:
        self._retry_count += 1
        if self._retry_count >= RETRY_POLL_MAXIMUM:
            # Only log the warning when transitioning to unavailable
            if self.available:
                _LOGGER.warning(
                    "Failed to update LinkPlay device %s after %s retries, "
                    "marking unavailable: %s",
                    self._bridge.device.name or self.entity_id,
                    RETRY_POLL_MAXIMUM,
                    err,
                )
            self._attr_available = False
        else:
            # Log debug/info for intermittent failures during retry period
            _LOGGER.debug(
                "Failed to update LinkPlay device %s, retry %s/%s: %s",
                self._bridge.device.name or self.entity_id,
                self._retry_count,
                RETRY_POLL_MAXIMUM,
                err,
            )
            # Entity remains available during these initial retries
            # self.available remains its current state (True if previously working)

    except Exception as err:
        # Catch any other unexpected errors during the update
        _LOGGER.exception(
            "Unexpected error updating LinkPlay entity %s, marking unavailable",
            self._bridge.device.name or self.entity_id,
        )
        self._attr_available = False
        # Depending on policy, you might want to re-raise this as HomeAssistantError
        # if it indicates a more severe, unrecoverable problem for core handling.
        # For instance:
        # raise HomeAssistantError(
        # f"Unexpected error during LinkPlay update for {self.entity_id}: {err}"
        # ) from err
```

By implementing these changes, the `LinkPlayMediaPlayerEntity` will correctly manage its `available` state based on its ability to fetch data from the device, adhering to the `entity-unavailable` rule. The existing retry mechanism (`RETRY_POLL_MAXIMUM`) is a reasonable approach, allowing for transient network issues before marking the entity unavailable.

_Created at 2025-05-11 14:59:12. Prompt tokens: 11726, Output tokens: 1872, Total tokens: 19813_
