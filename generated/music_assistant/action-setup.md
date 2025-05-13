# music_assistant: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `action-setup` rule requires that service actions are registered in the `async_setup` method of an integration. This ensures that service definitions (including their schemas) are available for validation (e.g., in automations) even if the associated configuration entry is not loaded. If a service depends on a loaded configuration entry, its handler should check the entry's status and raise `ServiceValidationError` if it's not loaded or invalid.

The `music_assistant` integration defines two types of services:

1.  **Global Services** (`search`, `get_library`):
    *   These are registered in `homeassistant/components/music_assistant/actions.py` via the `register_actions` function, which is called from `async_setup` in `homeassistant/components/music_assistant/__init__.py`.
    *   The service handlers (`handle_search`, `handle_get_library`) use a helper `get_music_assistant_client` which correctly takes a `config_entry_id`, checks if the entry exists and is loaded, and raises `ServiceValidationError` if not.
    *   This part of the integration **complies** with the rule.

2.  **Entity Services** (`play_media`, `play_announcement`, `transfer_queue`, `get_queue`):
    *   These services are associated with the `media_player` entities provided by `music_assistant`.
    *   They are registered in `homeassistant/components/music_assistant/media_player.py` within the `async_setup_entry` function using `platform.async_register_entity_service`.
    *   Crucially, for `play_media`, `play_announcement`, and `transfer_queue`, their schemas are defined directly in Python code alongside the registration call within `async_setup_entry`. For example, `SERVICE_PLAY_MEDIA_ADVANCED` (which is `play_media`):
        ```python
        # homeassistant/components/music_assistant/media_player.py
        platform.async_register_entity_service(
            SERVICE_PLAY_MEDIA_ADVANCED,
            { # Schema defined in-code
                vol.Required(ATTR_MEDIA_ID): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(ATTR_MEDIA_TYPE): vol.Coerce(MediaType),
                # ... other schema details ...
            },
            "_async_handle_play_media", # Entity method
        )
        ```
    *   Registering services (and their schemas defined in code) within `async_setup_entry` means they are only known to Home Assistant after a config entry has been successfully loaded and the platform setup has run. If no `music_assistant` config entry is loaded, these service definitions are not available, preventing validation of automations that use them. This directly contravenes the reasoning behind the `action-setup` rule: "the service actions are only available when there is a loaded entry. This is not ideal, since this way we can't validate automations users create that use these service actions, since it is possible that the configuration entry could not be loaded."
    *   Although `services.yaml` exists, schemas defined programmatically during registration typically override those in `services.yaml`. Even if `services.yaml` were the sole source for schemas, the rule pertains to the registration of the service action itself occurring in `async_setup`.
    *   This part of the integration does **not comply** with the rule.

Because the entity services are registered in `async_setup_entry` with their schemas defined in code, the integration does not fully follow the `action-setup` rule.

## Suggestions

To make the `music_assistant` integration compliant with the `action-setup` rule, the entity services (`play_media`, `play_announcement`, `transfer_queue`, `get_queue`) should be refactored. The recommended approach is to convert them into global services that are registered in `async_setup` and explicitly handle the target entity.

1.  **Transition Entity Services to Global Services:**
    Modify these services so they are no longer "entity services" tied to the `target` field in `services.yaml` but become global services under the `music_assistant` domain.

2.  **Register in `async_setup`:**
    Move the registration of these services from `media_player.py`'s `async_setup_entry` to the main integration `async_setup` (e.g., by adding them to `homeassistant/components/music_assistant/actions.py` and ensuring `register_actions` handles them). Use `hass.services.async_register`.

3.  **Modify Service Schemas:**
    *   Update `homeassistant/components/music_assistant/services.yaml`:
        *   For each affected service, remove the `target:` key.
        *   Add a new required field, for example, `entity_id`, to the `fields:` section. This field will specify the target `media_player` entity.
    *   Ensure the `vol.Schema` used with `hass.services.async_register` in `actions.py` matches this new structure, including the `entity_id` field.

4.  **Update Service Handlers:**
    The new global service handlers (e.g., in `actions.py`) must:
    *   Accept `call: ServiceCall`.
    *   Extract the `entity_id` from `call.data`.
    *   Verify the `entity_id`:
        *   Check if the entity exists using `hass.states.get(entity_id)` or `er.async_get(hass).async_get(entity_id)`.
        *   If the entity is not found, not a `music_assistant` media player, or otherwise unavailable (which can happen if its config entry is not loaded, or the entity is disabled), raise `ServiceValidationError` with an appropriate message (e.g., "Target entity {entity_id} not found or associated Music Assistant instance is not loaded.").
    *   If the entity is valid and available, obtain the `MusicAssistantPlayer` Python instance. This can be challenging for global services. A common pattern is for the platform to store its entity instances in `hass.data[DOMAIN][config_entry_id][<platform_key>]` which the global service handler might then access. Alternatively, the Home Assistant core's `MediaPlayer` component (accessed via `hass.data["media_player"]`) has a `get_entity(entity_id)` method that can retrieve the entity instance.
    *   Call the appropriate method on the `MusicAssistantPlayer` instance (e.g., `_async_handle_play_media`), passing the necessary arguments from `call.data`. The original entity methods might need slight adjustments if their signature was tied to the `platform.async_register_entity_service` schema.

**Example: Refactoring `play_media` (Conceptual)**

*   **`services.yaml` change for `play_media`:**
    ```yaml
    # Remove 'target:'
    # play_media:
    #   target:
    #     entity:
    #       domain: media_player
    #       integration: music_assistant
    play_media: # Becomes a global service
      fields:
        entity_id: # New field
          required: true
          description: "The target Music Assistant media player entity."
          example: "media_player.music_assistant_player"
          selector:
            entity:
              domain: media_player
              integration: music_assistant
        # ... existing fields for play_media (media_id, media_type, etc.)
    ```

*   **New handler in `actions.py`:**
    ```python
    from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
    from homeassistant.components.media_player import MediaPlayerEntity
    from homeassistant.const import ATTR_ENTITY_ID # Ensure this is imported or defined
    # ... other necessary imports from music_assistant ...

    async def handle_global_play_media(call: ServiceCall) -> None:
        """Handle the global play_media service call for Music Assistant."""
        hass = call.hass
        entity_id = call.data.get(ATTR_ENTITY_ID)

        if not entity_id:
            raise ServiceValidationError(f"'{ATTR_ENTITY_ID}' is required.")

        media_player_component = hass.data.get(MEDIA_PLAYER_DOMAIN)
        if not media_player_component:
            # This should ideally not happen if media_player component is loaded
            raise ServiceValidationError("Media player component not available.")

        entity = media_player_component.get_entity(entity_id)

        if not entity:
            raise ServiceValidationError(
                f"Entity {entity_id} not found. It may be disabled or the Music Assistant "
                "instance it belongs to is not currently loaded."
            )

        # Check if it's a MusicAssistantPlayer instance
        # (actual class MusicAssistantPlayer is in .media_player)
        # Need to import MusicAssistantPlayer carefully to avoid circular deps if actions.py is too core.
        # For this example, assume it's available or use a isinstance check with a more generic base if possible.
        # from ..media_player import MusicAssistantPlayer # Example import
        # if not isinstance(entity, MusicAssistantPlayer):
        #    raise ServiceValidationError(f"Entity {entity_id} is not a Music Assistant player.")


        # Ensure the entity is a MusicAssistantPlayer, otherwise, cast or handle error
        # This check can be made more specific by importing MusicAssistantPlayer
        if not hasattr(entity, "_async_handle_play_media"):
             raise ServiceValidationError(f"Entity {entity_id} is not a valid Music Assistant player or is not fully initialized.")

        # Call the original handler method on the entity instance
        # Note: _async_handle_play_media expects specific parameters, not the raw ServiceCall object.
        # You need to extract them from call.data.
        try:
            await entity._async_handle_play_media(
                media_id=call.data.get(ATTR_MEDIA_ID),
                media_type=call.data.get(ATTR_MEDIA_TYPE),
                enqueue=call.data.get(ATTR_MEDIA_ENQUEUE),
                artist=call.data.get(ATTR_ARTIST), # Assuming ATTR_ARTIST is defined and used
                album=call.data.get(ATTR_ALBUM),   # Assuming ATTR_ALBUM is defined and used
                radio_mode=call.data.get(ATTR_RADIO_MODE),
            )
        except HomeAssistantError: # Catch errors from the entity method if necessary
            raise
        except Exception as e: # Catch unexpected errors
            raise ServiceValidationError(f"Error calling play_media on {entity_id}: {e}") from e

    # In register_actions(hass):
    hass.services.async_register(
        DOMAIN,
        SERVICE_PLAY_MEDIA_ADVANCED, # "play_media"
        handle_global_play_media,
        schema=vol.Schema({ # Define schema including ATTR_ENTITY_ID
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
            vol.Required(ATTR_MEDIA_ID): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(ATTR_MEDIA_TYPE): vol.Coerce(MediaType),
            vol.Optional(ATTR_MEDIA_ENQUEUE): vol.Coerce(QueueOption),
            vol.Optional(ATTR_ARTIST): cv.string,
            vol.Optional(ATTR_ALBUM): cv.string,
            vol.Optional(ATTR_RADIO_MODE): vol.Coerce(bool),
        }),
    )
    ```

This refactoring ensures all service definitions and registrations occur in `async_setup`, aligning with the rule's requirements for validation and error handling. Repeat this pattern for `play_announcement`, `transfer_queue`, and `get_queue`.

_Created at 2025-05-13 09:58:12. Prompt tokens: 30232, Output tokens: 2829, Total tokens: 45437_
