```markdown
# samsungtv: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **todo**                                                                 |

## Overview

This rule requires that entities subscribe to events in `async_added_to_hass` and unsubscribe in `async_will_remove_from_hass` to prevent memory leaks and ensure resources are correctly managed during the entity's lifecycle. The recommended pattern for managing unsubscribe callbacks is using `self.async_on_remove()`.

The rule applies to the `samsungtv` integration as its entities (`SamsungTVDevice`, `SamsungTVRemote`, inheriting from `SamsungTVEntity`) may subscribe to events from the underlying libraries or integration components.

Upon reviewing the code:

1.  **Base Entity (`SamsungTVEntity`):** In `async_added_to_hass`, the base entity registers a `PluggableAction` for the device's "turn on" trigger. This registration correctly uses `self.async_on_remove`:
    ```python
    if (entry := self.registry_entry) and entry.device_id:
        self.async_on_remove(
            self._turn_on_action.async_register(
                self.hass, async_get_turn_on_trigger(entry.device_id)
            )
        )
    ```
    This part correctly follows the rule.

2.  **Media Player Entity (`SamsungTVDevice`):**
    *   In `async_added_to_hass`, the entity registers the `_app_list_callback` method with the bridge:
        ```python
        self._bridge.register_app_list_callback(self._app_list_callback)
        ```
        This `_app_list_callback` is invoked by the bridge when the TV's app list is received via the websocket connection. This is a form of event subscription where the entity receives updates from the integration's communication layer.
    *   There is currently **no corresponding unregistration or unsubscribe** call for the `_app_list_callback` in `async_will_remove_from_hass`. The `SamsungTVBridge` class holds a reference to this callback (`self._app_list_callback`), and without unregistering, the `SamsungTVDevice` entity instance cannot be fully garbage collected after it is removed, leading to a potential memory leak.
    *   The entity also handles UPNP subscriptions via the `async_upnp_client` library in `_async_startup_dmr`. The `async_upnp_client` library manages its own subscription lifecycle, which is started in `async_added_to_hass` (via `_async_extra_update` which is called after `async_added_to_hass`) and shut down in `async_will_remove_from_hass` via the `_async_shutdown_dmr` method. This pattern of managing the library object's lifecycle is acceptable for libraries that handle internal subscriptions.

3.  **Remote Entity (`SamsungTVRemote`):** This entity does not appear to subscribe to any events directly within its lifecycle methods beyond what is handled by the base class and the `CoordinatorEntity` parent, which manages the coordinator listener. This part follows the rule.

The violation stems specifically from the custom callback registration for the app list in `SamsungTVDevice` without a corresponding unregistration. Therefore, the integration does not fully follow the rule.

## Suggestions

To comply with the `entity-event-setup` rule, the `SamsungTVDevice` entity's subscription to the app list callback needs to be properly managed using `self.async_on_remove()`.

1.  **Modify `SamsungTVBridge`:** Update the `register_app_list_callback` method in `homeassistant/components/samsungtv/bridge.py` to return an unsubscribe function. This function should remove the stored callback reference. A simple way is to store the callback in a list or directly, and the unsubscribe function clears it.

    ```python
    # homeassistant/components/samsungtv/bridge.py
    
    class SamsungTVBridge(ABC):
        # ... other methods ...
        _app_list_callback: Callable[[dict[str, str]], None] | None = None # Store a single callback

        def register_app_list_callback(
            self, func: Callable[[dict[str, str]], None]
        ) -> Callable[[], None]:
            """Register app_list callback function and return unsubscribe."""
            # Store the new callback, overwriting any previous one (only one entity per bridge)
            self._app_list_callback = func

            @callback
            def unsubscribe() -> None:
                """Unregister the callback."""
                if self._app_list_callback == func: # Ensure we only remove THIS callback
                    self._app_list_callback = None

            return unsubscribe

        def _notify_app_list_callback(self, app_list: dict[str, str]) -> None:
            """Notify update config callback."""
            # Use call_soon_threadsafe if the callback might be called from a thread
            # (doesn't seem to be the case here, but good practice if unsure)
            if self._app_list_callback is not None:
                 self.hass.async_add_job(self._app_list_callback, app_list) # Or hass.async_run_hass_job
            # self.hass.async_run_callback(self._app_list_callback, app_list) # Alternative for async callback
    ```
    *(Note: The current implementation already stores only one callback, so simply setting it to None in unsubscribe is sufficient if only one entity type registers this callback per bridge)*. If multiple entity types needed to register, a list would be necessary.

2.  **Modify `SamsungTVDevice`:** In `homeassistant/components/samsungtv/media_player.py`, update the `async_added_to_hass` method to capture the unsubscribe function and pass it to `self.async_on_remove`.

    ```python
    # homeassistant/components/samsungtv/media_player.py
    
    class SamsungTVDevice(SamsungTVEntity, MediaPlayerEntity):
        # ... __init__ and other methods ...

        async def async_added_to_hass(self) -> None:
            """Run when entity about to be added to hass."""
            await super().async_added_to_hass()

            # Capture the unsubscribe function and pass it to async_on_remove
            unsubscribe_app_list = self._bridge.register_app_list_callback(self._app_list_callback)
            self.async_on_remove(unsubscribe_app_list)

            # ... rest of the async_added_to_hass method ...
            await self._async_extra_update()
            self.coordinator.async_extra_update = self._async_extra_update
            # ... etc ...
    ```

These changes ensure that when the `SamsungTVDevice` entity is removed, the reference held by the bridge to its `_app_list_callback` is released, preventing memory leaks and adhering to the rule.

_Created at 2025-05-25 11:28:22. Prompt tokens: 30302, Output tokens: 1662, Total tokens: 34433_
