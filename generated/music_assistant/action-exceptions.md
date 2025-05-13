# music_assistant: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `action-exceptions` rule applies to the `music_assistant` integration because it defines and handles several service actions, both at the integration level (e.g., `search`, `get_library`) and at the media player entity level (e.g., `play_media`, `transfer_queue`, standard media controls).

The integration currently does NOT fully follow the rule due to the following reasons:

1.  **Inconsistent `MusicAssistantError` Handling in `actions.py`:**
    The service handlers `handle_search` and `handle_get_library` in `homeassistant/components/music_assistant/actions.py` call methods on the `MusicAssistantClient` (e.g., `mass.music.search(...)`, `mass.music.get_library_albums(...)`). These client methods can raise `MusicAssistantError` or its subclasses (defined in `music_assistant_client.exceptions` or `music_assistant_models.errors`). These exceptions are not explicitly caught and re-raised as `HomeAssistantError` or `ServiceValidationError` as required by the rule. For example, if `mass.music.search()` fails due to a provider issue within Music Assistant, it might raise a `ProviderUnavailableError` (a subclass of `MusicAssistantError`), which would then propagate uncaught by the service handler, instead of being converted to a `HomeAssistantError`.

2.  **Misclassification of Exceptions in `media_player.py` Entity Services:**
    Several custom entity services in `homeassistant/components/music_assistant/media_player.py` raise `HomeAssistantError` for conditions that, according to the rule, should be `ServiceValidationError` because they stem from incorrect user input or referencing non-existent items:
    *   In `_async_handle_play_media`: If `media_uris` remains empty after trying to resolve `media_id`, it raises `HomeAssistantError(f"Could not resolve {media_id} to playable media item")`. This should be a `ServiceValidationError` as the provided `media_id` (user input) could not be resolved.
    *   In `_async_handle_transfer_queue`: If a `source_player` entity ID provided by the user does not exist, it raises `HomeAssistantError("Source player not available.")`. This should be a `ServiceValidationError`.
    *   In `_async_handle_get_queue`: If there is no active queue for the player, it raises `HomeAssistantError("No active queue found")`. This could be interpreted as the user trying to get details for a non-existent queue for that player state, warranting a `ServiceValidationError`.

3.  **Over-Generalization by `@catch_musicassistant_error` Decorator:**
    The `@catch_musicassistant_error` decorator in `homeassistant/components/music_assistant/media_player.py` is a good general mechanism. It catches `MusicAssistantError` and re-raises it as `HomeAssistantError(str(err)) from err`. However, the `music-assistant-client` library can raise specific subclasses of `MusicAssistantError`, such as `MediaNotFoundError`, when an item referenced by the user (e.g., via a URI or ID in `play_media`) does not exist. According to the rule, "referencing something that does not exist" should raise a `ServiceValidationError`. The current decorator converts these specific "not found" errors into generic `HomeAssistantError`s, which is not the most appropriate classification.

4.  **Suppression of `MediaNotFoundError`:**
    In `_async_handle_play_media` within `homeassistant/components/music_assistant/media_player.py`, there's a `with suppress(MediaNotFoundError):` block when attempting to get a media item by numeric ID:
    ```python
    if media_type and media_id_str.isnumeric():
        with suppress(MediaNotFoundError): # This is problematic
            item = await self.mass.music.get_item(
                MediaType(media_type), media_id_str, "library"
            )
            # ...
    ```
    If a user provides a specific numeric `media_id_str` (implying a direct reference to a library item) and it's not found, `MediaNotFoundError` should not be suppressed. Instead, it should be caught and re-raised as a `ServiceValidationError` to inform the user about their incorrect input.

While the integration makes attempts to handle errors (notably with the `@catch_musicassistant_error` decorator and some `ServiceValidationError` instances in `actions.py` for config entry issues), the classification and completeness of exception handling in service actions need improvement to fully comply with the `action-exceptions` rule.

## Suggestions

To make the `music_assistant` integration compliant with the `action-exceptions` rule, consider the following changes:

1.  **Improve Exception Handling in `actions.py`:**
    For `handle_search` and `handle_get_library` in `homeassistant/components/music_assistant/actions.py`:
    Wrap the calls to `mass.music.*` methods (e.g., `mass.music.search`, `mass.music.get_library_albums`) in `try...except` blocks to catch `MusicAssistantError` and its subclasses. Generally, these should be re-raised as `HomeAssistantError`, as they often indicate operational issues with the Music Assistant server or its providers.

    Example for `handle_search`:
    ```python
    async def handle_search(call: ServiceCall) -> ServiceResponse:
        mass = get_music_assistant_client(call.hass, call.data[ATTR_CONFIG_ENTRY_ID])
        # ... (other setup) ...
        try:
            search_results = await mass.music.search(
                search_query=search_name,
                media_types=call.data.get(ATTR_MEDIA_TYPE, MediaType.ALL),
                limit=call.data[ATTR_LIMIT],
                library_only=call.data[ATTR_LIBRARY_ONLY],
            )
        except MusicAssistantError as err:
            # Log err if needed for debugging
            raise HomeAssistantError(f"Error during search operation: {err}") from err
        # ... (process results) ...
    ```
    Apply similar error handling to the various `await mass.music.get_library_...` calls in `handle_get_library`.

2.  **Correct Exception Types in `media_player.py` Entity Services:**
    *   In `_async_handle_play_media`:
        *   Change:
            ```python
            if not media_uris:
                raise HomeAssistantError(
                    f"Could not resolve {media_id} to playable media item"
                )
            ```
            To:
            ```python
            if not media_uris:
                raise ServiceValidationError(
                    f"Could not resolve '{media_id}' to a playable media item. "
                    "Please check the name, artist, or album if provided, or ensure the URI/ID is correct."
                )
            ```
    *   In `_async_handle_transfer_queue`:
        *   Change:
            ```python
            if (entity := entity_registry.async_get(source_player)) is None:
                raise HomeAssistantError("Source player not available.")
            ```
            To:
            ```python
            if source_player and (entity := entity_registry.async_get(source_player)) is None: # Check if source_player was provided
                raise ServiceValidationError(f"Source player entity '{source_player}' not found.")
            ```
    *   In `_async_handle_get_queue`:
        *   Change:
            ```python
            if not self.active_queue:
                raise HomeAssistantError("No active queue found")
            ```
            To:
            ```python
            if not self.active_queue:
                raise ServiceValidationError("This player does not have an active queue for which to retrieve details.")
            ```

3.  **Refine or Augment `@catch_musicassistant_error` Decorator:**
    The decorator should ideally differentiate between `MusicAssistantError` types that signify user error versus operational errors.
    *   **Option 1: Enhance the decorator:**
        Modify `catch_musicassistant_error` to check for specific error types like `MediaNotFoundError`:
        ```python
        # In homeassistant/components/music_assistant/media_player.py
        from music_assistant_models.errors import MediaNotFoundError # Add import

        # ...
        async def wrapper(
            self: MusicAssistantPlayer, *args: P.args, **kwargs: P.kwargs
        ) -> _R:
            """Catch Music Assistant errors and convert to Home Assistant error."""
            try:
                return await func(self, *args, **kwargs)
            except MediaNotFoundError as err: # Catch specific "not found" user errors
                raise ServiceValidationError(f"Requested media item not found: {err}") from err
            # Potentially add other isinstance checks for errors like ActionUnavailable if they map to user error
            except MusicAssistantError as err: # General operational errors
                error_msg = str(err) or err.__class__.__name__
                raise HomeAssistantError(error_msg) from err
        ```
    *   **Option 2: Specific handling within methods:**
        Alternatively, for calls within decorated methods that are known to raise `MediaNotFoundError` due to invalid user input (e.g., playing a specific URI that doesn't exist), catch `MediaNotFoundError` explicitly within the method body and raise `ServiceValidationError` before the decorator's general `MusicAssistantError` catch.

4.  **Address `MediaNotFoundError` Suppression in `_async_handle_play_media`:**
    Remove `with suppress(MediaNotFoundError):` when fetching an item by a numeric ID. If `media_id_str.isnumeric()` and `media_type` are provided, a `MediaNotFoundError` from `self.mass.music.get_item` should be caught and re-raised as a `ServiceValidationError`.

    Example modification in `_async_handle_play_media`:
    ```python
    # ...
    for media_id_str in media_id:
        # ...
        if media_type and media_id_str.isnumeric():
            try:
                item = await self.mass.music.get_item(
                    MediaType(media_type), media_id_str, "library"
                )
                if isinstance(item, MediaItemType | ItemMapping) and item.uri:
                    media_uris.append(item.uri)
                continue # Found by numeric ID
            except MediaNotFoundError as err:
                raise ServiceValidationError(
                    f"Media item with ID '{media_id_str}' of type '{media_type}' not found in the library."
                ) from err
        # ... (rest of the resolution logic) ...
    ```

By implementing these suggestions, the `music_assistant` integration will better align with the `action-exceptions` rule, providing clearer feedback to users in case of errors and properly distinguishing between user input errors and operational failures.

_Created at 2025-05-13 10:07:51. Prompt tokens: 30108, Output tokens: 2618, Total tokens: 39464_
