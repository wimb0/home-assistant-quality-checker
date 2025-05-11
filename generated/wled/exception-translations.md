# wled: exception-translations

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [exception-translations](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/exception-translations)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `exception-translations` rule requires that error messages shown to the user, originating from `HomeAssistantError` or its subclasses, are translatable. This is achieved by raising such exceptions with `translation_domain` and `translation_key` parameters, and defining the corresponding messages in the integration's `strings.json` file under an `exceptions` key.

This rule applies to the `wled` integration because it raises exceptions derived from `HomeAssistantError` (specifically `HomeAssistantError` itself and `UpdateFailed`) to communicate issues to the user, such as API communication failures or update problems.

The integration currently does **not** follow this rule due to the following:

1.  **Hardcoded exception messages in `coordinator.py`:**
    *   In `WLEDDataUpdateCoordinator._async_update_data()`, `UpdateFailed` (a subclass of `HomeAssistantError`) is raised with an f-string:
        ```python
        # coordinator.py
        except WLEDError as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error
        ```
    *   Similarly, in `WLEDReleasesDataUpdateCoordinator._async_update_data()`:
        ```python
        # coordinator.py
        except WLEDError as error:
            raise UpdateFailed(f"Invalid response from GitHub API: {error}") from error
        ```
    These messages are not translatable.

2.  **Hardcoded exception messages in `helpers.py`:**
    *   The `wled_exception_handler` decorator, used by many entity service calls (e.g., in `light.py`, `switch.py`, `button.py`), raises `HomeAssistantError` with hardcoded strings:
        ```python
        # helpers.py
        except WLEDConnectionError as error:
            # ...
            raise HomeAssistantError("Error communicating with WLED API") from error

        except WLEDError as error:
            raise HomeAssistantError("Invalid response from WLED API") from error
        ```
    These messages are not translatable.

3.  **Missing `exceptions` section in `strings.json`:**
    *   The `strings.json` file (and consequently `translations/en.json`) does not contain an `"exceptions"` top-level key where translated messages for these exceptions would be defined.

While the config flow (`config_flow.py`) uses translatable error messages through the `errors` dictionary and `async_abort` reasons (which are looked up in `strings.json` under `config.error` and `config.abort`), the exceptions raised during runtime operations (like entity service calls or coordinator updates) do not use the required translation mechanism for exceptions.

## Suggestions

To make the `wled` integration compliant with the `exception-translations` rule, the following changes are recommended:

1.  **Modify `coordinator.py` to use translatable `UpdateFailed` exceptions:**

    Update the `_async_update_data` methods in both coordinators to raise `UpdateFailed` with `translation_domain`, `translation_key`, and `translation_placeholders` (if needed).

    For `WLEDDataUpdateCoordinator`:
    ```python
    # coordinator.py
    from .const import DOMAIN # Ensure DOMAIN is imported

    # ...
    async def _async_update_data(self) -> WLEDDevice:
        """Fetch data from WLED."""
        try:
            device = await self.wled.update()
        except WLEDError as error:
            # MODIFIED LINE
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="api_error",
                translation_placeholders={"error": str(error)},
            ) from error
        # ...
    ```

    For `WLEDReleasesDataUpdateCoordinator`:
    ```python
    # coordinator.py
    from .const import DOMAIN # Ensure DOMAIN is imported

    # ...
    async def _async_update_data(self) -> Releases:
        """Fetch release data from WLED."""
        try:
            return await self.wled.releases()
        except WLEDError as error:
            # MODIFIED LINE
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="github_api_error",
                translation_placeholders={"error": str(error)},
            ) from error
    ```

2.  **Modify `helpers.py` to use translatable `HomeAssistantError` exceptions:**

    Update the `wled_exception_handler` to raise `HomeAssistantError` with `translation_domain` and `translation_key`.

    ```python
    # helpers.py
    from .const import DOMAIN # Ensure DOMAIN is imported

    # ...
    def wled_exception_handler[_WLEDEntityT: WLEDEntity, **_P](
        func: Callable[Concatenate[_WLEDEntityT, _P], Coroutine[Any, Any, Any]],
    ) -> Callable[Concatenate[_WLEDEntityT, _P], Coroutine[Any, Any, None]]:
        # ...
        async def handler(self: _WLEDEntityT, *args: _P.args, **kwargs: _P.kwargs) -> None:
            try:
                await func(self, *args, **kwargs)
                self.coordinator.async_update_listeners()

            except WLEDConnectionError as error:
                self.coordinator.last_update_success = False
                self.coordinator.async_update_listeners()
                # MODIFIED LINE
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="communication_error",
                ) from error

            except WLEDError as error:
                # MODIFIED LINE
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_response_error",
                ) from error
        return handler
    ```

3.  **Add an `exceptions` section to `strings.json`:**

    Define the translation keys used above in the `strings.json` file. The corresponding entries should also be added to `translations/en.json` and any other translation files.

    ```json
    // strings.json
    {
      "config": {
        // ... existing config flow strings
      },
      "options": {
        // ... existing options strings
      },
      "entity": {
        // ... existing entity strings
      },
      "exceptions": {
        "communication_error": {
          "message": "Error communicating with the WLED device. Please ensure it's reachable and responsive."
        },
        "invalid_response_error": {
          "message": "Received an invalid response from the WLED device."
        },
        "api_error": {
          "message": "Failed to update WLED data due to an API error: {error}"
        },
        "github_api_error": {
          "message": "Failed to fetch WLED release information from GitHub: {error}"
        }
      }
    }
    ```

**Why these changes satisfy the rule:**

*   By raising `HomeAssistantError` and `UpdateFailed` (a subclass of `HomeAssistantError`) with `translation_domain` and `translation_key`, the error messages become translatable by Home Assistant's core localization system.
*   Defining these translation keys and their corresponding messages in `strings.json` provides the necessary English (and subsequently other language) strings for display.
*   This approach ensures that users worldwide can understand error messages in their preferred language, improving usability.

_Created at 2025-05-10 23:04:04. Prompt tokens: 21582, Output tokens: 1814, Total tokens: 27131_
