# linkplay: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `config-entry-unloading` rule requires that integrations implement `async_unload_entry` to properly clean up all resources, subscriptions, and connections established during the `async_setup_entry` phase. This allows users to remove or reload the integration without restarting Home Assistant.

The `linkplay` integration **applies** to this rule as it is configured via config entries.

The integration **partially** follows the rule:
1.  It implements the `async_unload_entry` function in `__init__.py`.
2.  Inside `async_unload_entry`, it correctly calls `hass.config_entries.async_unload_platforms(entry, PLATFORMS)` to unload associated entities from platforms like `media_player` and `button`.
3.  It performs specific cleanup for the `LinkPlayBridge` associated with the config entry by calling `await controller.remove_bridge(bridge)` where `controller` is a shared `LinkPlayController` instance. This removes the entry-specific bridge from the shared controller's management.
4.  The `LinkPlayBridge` instance itself, stored in `entry.runtime_data.bridge`, will be garbage collected after the entry is successfully unloaded and `runtime_data` is cleared by Home Assistant.
5.  A shared `aiohttp.ClientSession` is used, obtained via `async_get_client_session` in `utils.py`. Its lifecycle is tied to `EVENT_HOMEASSISTANT_CLOSE`, meaning it's designed to persist for the duration of Home Assistant's runtime, which is acceptable for a shared resource across multiple config entries of the same domain.

However, there is one area where cleanup is incomplete:
*   In `media_player.py`, the `LinkPlayMediaPlayerEntity.async_added_to_hass` method adds an entry to a shared dictionary: `self.hass.data[DOMAIN][SHARED_DATA].entity_to_bridge[self.entity_id] = self._bridge.device.uuid`. This dictionary (`entity_to_bridge`) is part of `LinkPlaySharedData` stored in `hass.data[DOMAIN][SHARED_DATA]`.
*   When a config entry is unloaded, its associated `LinkPlayMediaPlayerEntity` entities are removed. However, there is no corresponding logic to remove their entries from this shared `entity_to_bridge` dictionary. This results in stale entries (mapping an `entity_id` that no longer exists to a `bridge_uuid`) persisting in `hass.data`, leading to a minor memory leak and potentially stale data if this dictionary is used elsewhere expecting live entities.

Because not all resources (specifically, entries in the `entity_to_bridge` map) tied to the config entry's entities are cleaned up, the integration does not fully comply with the rule.

## Suggestions

To fully comply with the `config-entry-unloading` rule, the stale entries in the `hass.data[DOMAIN][SHARED_DATA].entity_to_bridge` dictionary should be removed when the corresponding media player entity is removed. This can be achieved by implementing the `async_will_remove_from_hass` method in the `LinkPlayMediaPlayerEntity` class.

**Specific Change:**

Modify `media_player.py` to include the `async_will_remove_from_hass` method in the `LinkPlayMediaPlayerEntity` class:

```python
# ... other imports ...
from .const import DOMAIN, SHARED_DATA # Ensure SHARED_DATA is imported if not already
from .const import LinkPlaySharedData # Import the type hint if needed

_LOGGER = logging.getLogger(__name__)
# ... rest of the file ...

class LinkPlayMediaPlayerEntity(LinkPlayBaseEntity, MediaPlayerEntity):
    # ... existing code ...

    async def async_added_to_hass(self) -> None:
        """Handle common setup when added to hass."""
        await super().async_added_to_hass()
        # Ensure shared data structure exists
        self.hass.data.setdefault(DOMAIN, {}).setdefault(SHARED_DATA, LinkPlaySharedData(controller=None, entity_to_bridge={})) # Or however it's initialized
        
        # It's safer to access shared_data after ensuring it and its keys exist.
        # The controller part of LinkPlaySharedData is initialized in __init__.py,
        # so this part mainly ensures entity_to_bridge dict is present.
        # A more robust way might be to ensure LinkPlaySharedData is fully initialized 
        # before entities are added or to handle potential KeyError.
        
        shared_data_obj: LinkPlaySharedData = self.hass.data[DOMAIN][SHARED_DATA]
        shared_data_obj.entity_to_bridge[self.entity_id] = self._bridge.device.uuid

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        try:
            shared_data_obj: LinkPlaySharedData = self.hass.data[DOMAIN][SHARED_DATA]
            if self.entity_id in shared_data_obj.entity_to_bridge:
                del shared_data_obj.entity_to_bridge[self.entity_id]
                _LOGGER.debug(
                    "Removed %s from entity_to_bridge map during unload", self.entity_id
                )
        except KeyError:
            # This might happen if DOMAIN or SHARED_DATA was unexpectedly removed,
            # or if entity_id was already removed.
            _LOGGER.debug(
                "Could not remove %s from entity_to_bridge map: shared data not found or key absent",
                self.entity_id,
            )

    # ... rest of the class ...
```

**Reasoning for Suggestion:**
The `async_will_remove_from_hass` method is called by Home Assistant just before an entity is removed from the system. This is the appropriate place for an entity to clean up any global registrations or resources it has created or is associated with. By removing its `entity_id` from the `entity_to_bridge` dictionary here, the integration ensures that this shared data structure does not accumulate stale entries when config entries (and their entities) are unloaded. This addresses the identified resource leak and brings the integration into full compliance with the `config-entry-unloading` rule.

_Created at 2025-05-11 14:57:46. Prompt tokens: 10800, Output tokens: 1538, Total tokens: 17353_
