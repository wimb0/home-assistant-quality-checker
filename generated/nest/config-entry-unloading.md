# nest: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `config-entry-unloading` rule applies to the `nest` integration because it uses config entries for its setup, as indicated by `config_flow: true` in its `manifest.json`. The rule requires that integrations implement `async_unload_entry` to clean up all resources (subscriptions, connections, listeners, etc.) established during `async_setup_entry`, allowing the integration to be unloaded and reloaded without a Home Assistant restart.

The `nest` integration partially follows this rule:
1.  It implements `async_unload_entry` in `homeassistant/components/nest/__init__.py`, which correctly calls `hass.config_entries.async_unload_platforms(entry, PLATFORMS)` to unload associated platform entities.
2.  It utilizes `entry.async_on_unload` to register cleanup callbacks for significant resources:
    *   `unsub()`: This function, which is `subscriber.stop_async()`, stops the `GoogleNestSubscriber`, effectively terminating its connection to Google's Pub/Sub service.
    *   An `EVENT_HOMEASSISTANT_STOP` listener is also properly cleaned up.

However, there is a resource that is not properly cleaned up upon config entry unload:
In `homeassistant/components/nest/media_source.py`, the `NestEventMediaStore` class initializes a periodic timer using `async_track_time_interval`:
```python
# homeassistant/components/nest/media_source.py
class NestEventMediaStore(EventMediaStore):
    def __init__(
        self,
        # ...
    ) -> None:
        # ...
        # Invoke garbage collection for orphaned files one per
        async_track_time_interval(  # This creates a persistent timer
            hass,
            self.async_remove_orphaned_media,
            datetime.timedelta(days=1),
        )
```
This timer is intended to clean up orphaned media files. When the `nest` config entry is unloaded, this timer is not cancelled. This constitutes a resource leak, as the timer callback (`async_remove_orphaned_media`) will continue to be invoked even after the integration is unloaded.

The current `async_unload_entry` in `homeassistant/components/nest/__init__.py` is:
```python
async def async_unload_entry(hass: HomeAssistant, entry: NestConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```
While this handles platform unloading, and `entry.async_on_unload` handles the subscriber, the timer in `NestEventMediaStore` remains active. The rule's example shows direct cleanup action within `async_unload_entry` (e.g., `entry.runtime_data.listener()`), which is appropriate for resources not managed by `entry.async_on_unload` or platform entity teardown.

Thus, the integration does not fully follow the rule because it fails to clean up all resources (specifically, the timer in `NestEventMediaStore`).

## Suggestions

To make the `nest` integration compliant with the `config-entry-unloading` rule, the timer created in `NestEventMediaStore` must be cancelled when the config entry is unloaded.

1.  **Modify `NestEventMediaStore` in `homeassistant/components/nest/media_source.py`:**
    *   Store the cancellation callback returned by `async_track_time_interval`.
    *   Add an `async_close` method to `NestEventMediaStore` to execute this cancellation callback.

    ```python
    # homeassistant/components/nest/media_source.py

    # ...
    from collections.abc import Callable # Add this import
    # ...

    class NestEventMediaStore(EventMediaStore):
        def __init__(
            self,
            hass: HomeAssistant,
            subscriber: GoogleNestSubscriber,
            store: Store[dict[str, Any]],
            media_path: str,
        ) -> None:
            """Initialize NestEventMediaStore."""
            self._hass = hass
            self._subscriber = subscriber
            self._store = store
            self._media_path = media_path
            self._data: dict[str, Any] | None = None
            self._devices: Mapping[str, str] | None = {}
            # Store the unsubscribe callback for the timer
            self._cleanup_timer_unsub: Callable[[], None] | None = None
            self._cleanup_timer_unsub = async_track_time_interval(
                hass,
                self.async_remove_orphaned_media,
                datetime.timedelta(days=1),
            )

        async def async_close(self) -> None:
            """Close the media store and clean up resources like timers."""
            _LOGGER.debug("Closing NestEventMediaStore and cancelling cleanup timer.")
            if self._cleanup_timer_unsub:
                self._cleanup_timer_unsub()
                self._cleanup_timer_unsub = None
            # If there are other resources in NestEventMediaStore that need closing,
            # they should be handled here.
            # Forcing a save of the Store object might be considered if essential on unload,
            # though async_delay_save typically handles persistence.
            # e.g., if self._data is not None: await self._store.async_save(self._data)

        # ... rest of the class ...
    ```

2.  **Update `async_unload_entry` in `homeassistant/components/nest/__init__.py`:**
    *   After successfully unloading platforms, retrieve the `NestEventMediaStore` instance from `entry.runtime_data`.
    *   Call its new `async_close` method.

    ```python
    # homeassistant/components/nest/__init__.py

    # ...

    async def async_unload_entry(hass: HomeAssistant, entry: NestConfigEntry) -> bool:
        """Unload a config entry."""
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        if unload_ok:
            # Clean up other resources managed by the integration
            if (
                entry.runtime_data
                and entry.runtime_data.subscriber
                and entry.runtime_data.subscriber.cache_policy
                and (store := entry.runtime_data.subscriber.cache_policy.store)
            ):
                if hasattr(store, "async_close") and callable(
                    getattr(store, "async_close")
                ):
                    _LOGGER.debug("Closing NestEventMediaStore")
                    await store.async_close() # type: ignore[attr-defined]
            
            # Optionally, clear runtime_data if it helps with garbage collection,
            # though not strictly required if all held resources are properly closed.
            # entry.runtime_data = None
    return unload_ok
    ```

**Why these changes satisfy the rule:**
*   The `NestEventMediaStore` now has a dedicated method (`async_close`) to clean up its internal resources, specifically the timer.
*   The `async_unload_entry` function in the main integration file (`__init__.py`) will now explicitly call this `async_close` method if the platform unloading is successful.
*   This ensures that the timer, which is a subscription-like resource, is properly terminated when the config entry is unloaded, preventing resource leaks and adhering to the rule's requirement to clean up all resources.
*   The `entry.async_on_unload` callbacks will still fire after `async_unload_entry` returns `True`, handling the `GoogleNestSubscriber` cleanup (`unsub`). The order of operations (platform unload, then `store.async_close()`, then `entry.async_on_unload` callbacks) ensures that components are shut down gracefully.

_Created at 2025-05-28 22:55:31. Prompt tokens: 32384, Output tokens: 1880, Total tokens: 41187_
