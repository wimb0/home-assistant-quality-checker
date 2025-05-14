# music_assistant: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `exception-translations` rule requires that user-facing error messages originating from exceptions that inherit `HomeAssistantError` are translatable. This involves raising such exceptions with `translation_domain` and `translation_key` parameters, and defining these keys in the `strings.json` file under a top-level `"exceptions"` key.

This rule applies to the `music_assistant` integration because it raises various exceptions derived from `HomeAssistantError` (such as `ConfigEntryNotReady`, `HomeAssistantError`, `ServiceValidationError`, `BrowseError`, `SearchError`) in different parts of its codebase, including setup, service calls, and media browsing, which can result in messages being displayed to the user.

The integration currently does **not** follow this rule.
1.  **Missing `"exceptions"` key in `strings.json`**: The `homeassistant/components/music_assistant/strings.json` file does not contain the required top-level `"exceptions": {}` block where these translations should be defined.
2.  **Untranslated exceptions raised**: Numerous instances exist where exceptions inheriting from `HomeAssistantError` are raised with hardcoded or f-string messages, rather than using `translation_domain` and `translation_key`.

Key areas where this is observed:

*   **`__init__.py` (Setup Process):**
    *   `ConfigEntryNotReady(f"Failed to connect to music assistant server {mass_url}")` (L60)
    *   `ConfigEntryNotReady(f"Invalid server version: {err}")` (L68) - Even though an issue is created with a translation key, the exception itself is not translated.
    *   `ConfigEntryNotReady(f"Unknown error connecting to the Music Assistant server {mass_url}")` (L73)
    *   `ConfigEntryNotReady("Music Assistant client not ready")` (L91)
    *   `raise ConfigEntryNotReady(listen_error) from listen_error` (L98) - `listen_error` is likely an untranslated string.

*   **`media_player.py` (Entity Logic and Services):**
    *   The `@catch_musicassistant_error` decorator catches `MusicAssistantError` (from the client library) and re-raises it as `HomeAssistantError(error_msg)`. The `error_msg` is a raw string from the original error, not a translation key.
        ```python
        # homeassistant/components/music_assistant/media_player.py L100-L103
        except MusicAssistantError as err:
            error_msg = str(err) or err.__class__.__name__
            raise HomeAssistantError(error_msg) from err
        ```
    *   `async_join_players`: `raise HomeAssistantError(f"Entity {child_entity_id} not found")` (L442)
    *   `_async_handle_play_media`: `raise HomeAssistantError(f"Could not resolve {media_id} to playable media item")` (L504)
    *   `_async_handle_transfer_queue`:
        *   `raise HomeAssistantError("Source player not specified and no playing player found.")` (L540)
        *   `raise HomeAssistantError("Source player not available.")` (L546)
    *   `_async_handle_get_queue`: `raise HomeAssistantError("No active queue found")` (L555)

*   **`media_browser.py`:**
    *   `raise BrowseError(f"Media not found: {media_content_type} / {media_content_id}")` (L101) - `BrowseError` is a subclass of `HomeAssistantError`.
    *   `raise SearchError(f"Error searching for {query.search_query}") from err` (L519) - `SearchError` is a subclass of `HomeAssistantError`.

*   **`actions.py` (Custom Services):**
    *   `get_music_assistant_client`:
        *   `raise ServiceValidationError("Entry not found")` (L43)
        *   `raise ServiceValidationError("Entry not loaded")` (L45)
    *   `handle_get_library`: `raise ServiceValidationError(f"Unsupported media type {media_type}")` (L176) - `ServiceValidationError` is a subclass of `HomeAssistantError`.

## Suggestions

To make the `music_assistant` integration compliant with the `exception-translations` rule, the following changes are recommended:

1.  **Add `"exceptions"` block to `strings.json`:**
    Modify `homeassistant/components/music_assistant/strings.json` to include a top-level `"exceptions"` key.

    ```json
    {
      "config": { ... },
      "issues": { ... },
      "services": { ... },
      "selector": { ... },
      "exceptions": {
        "example_key": {
          "message": "This is an example translatable exception message with a placeholder: {placeholder_name}."
        }
        // Add other exception keys here
      }
    }
    ```

2.  **Update Python code to use translatable exceptions:**
    For each instance where a `HomeAssistantError` (or its subclass) is raised with a hardcoded string, do the following:
    *   Define a unique translation key (e.g., `connect_failed`, `media_not_found`).
    *   Add this key and its corresponding user-friendly message to the `"exceptions"` block in `strings.json`. Use placeholders (e.g., `{url}`, `{details}`) in the message for dynamic content.
    *   Modify the `raise` statement in Python to use `translation_domain=DOMAIN`, `translation_key="your_new_key"`, and `translation_placeholders` if needed.

**Example 1: `ConfigEntryNotReady` in `__init__.py`**

*   **Current code (`__init__.py` L60):**
    ```python
    raise ConfigEntryNotReady(
        f"Failed to connect to music assistant server {mass_url}"
    ) from err
    ```

*   **Suggested `strings.json` addition:**
    ```json
    // inside "exceptions": { ... }
    "connect_failed": {
      "message": "Failed to connect to Music Assistant server at {url}."
    }
    ```

*   **Suggested Python code:**
    ```python
    from .const import DOMAIN # Ensure DOMAIN is imported

    # ...
    raise ConfigEntryNotReady(
        translation_domain=DOMAIN,
        translation_key="connect_failed",
        translation_placeholders={"url": mass_url},
    ) from err
    ```

**Example 2: `@catch_musicassistant_error` in `media_player.py`**

*   **Current code (`media_player.py` L100-L103):**
    ```python
    except MusicAssistantError as err:
        error_msg = str(err) or err.__class__.__name__
        raise HomeAssistantError(error_msg) from err
    ```

*   **Suggested `strings.json` addition:**
    ```json
    // inside "exceptions": { ... }
    "mass_client_error": {
      "message": "A communication error occurred with the Music Assistant server: {details}"
    }
    ```

*   **Suggested Python code:**
    ```python
    from .const import DOMAIN # Ensure DOMAIN is imported

    # ...
    except MusicAssistantError as err:
        error_msg = str(err) or err.__class__.__name__
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="mass_client_error",
            translation_placeholders={"details": error_msg},
        ) from err
    ```

**Example 3: `ServiceValidationError` in `actions.py`**

*   **Current code (`actions.py` L43):**
    ```python
    raise ServiceValidationError("Entry not found")
    ```

*   **Suggested `strings.json` addition:**
    ```json
    // inside "exceptions": { ... }
    "entry_not_found": {
      "message": "The configuration entry could not be found."
    }
    ```

*   **Suggested Python code:**
    ```python
    from .const import DOMAIN # Ensure DOMAIN is imported

    # ...
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="entry_not_found",
    )
    ```

**General Guidance:**
*   For exceptions like `ConfigEntryNotReady(listen_error)` where `listen_error` might be an opaque string from an external library, consider either mapping known `listen_error` values to specific translation keys or using a generic translation key like `"client_setup_failed"` with `{details: str(listen_error)}` as a placeholder.
*   Apply similar transformations to all identified instances of untranslated `HomeAssistantError` subclasses (`ConfigEntryNotReady`, `ServiceValidationError`, `BrowseError`, `SearchError`, and direct `HomeAssistantError` raises).
*   Ensure that the `DOMAIN` constant is correctly imported and used as the `translation_domain`.

_Created at 2025-05-14 13:42:50. Prompt tokens: 30166, Output tokens: 2225, Total tokens: 35691_
