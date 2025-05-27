# paperless_ngx: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [paperless_ngx](https://www.home-assistant.io/integrations/paperless_ngx/) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `reauthentication-flow` rule requires integrations that use authentication to provide a UI flow for users to update their credentials if they become invalid, without needing to delete and re-add the integration.

This rule **applies** to the `paperless_ngx` integration because it uses an API key (`CONF_API_KEY`) for authentication, as configured in `config_flow.py` and utilized by the `PaperlessCoordinator` in `coordinator.py`.

The integration currently does **not** follow this rule.
1.  **Missing Reauthentication Flow:** The `config_flow.py` file for `paperless_ngx` does not implement the `async_step_reauth` method or any associated reauthentication steps (e.g., `async_step_reauth_confirm`). This means there's no defined UI flow for users to enter new credentials when the existing ones fail.
2.  **Incorrect Exception Handling for Auth Errors:** In `coordinator.py`, when authentication-related errors from the `pypaperless` library occur (like `PaperlessInvalidTokenError`, `PaperlessInactiveOrDeletedError`, or `PaperlessForbiddenError`), the `PaperlessCoordinator` raises `ConfigEntryError` or `UpdateFailed`. To trigger Home Assistant's reauthentication mechanism, it should instead raise `homeassistant.exceptions.ConfigEntryAuthFailed`.

    *   In `PaperlessCoordinator._async_setup()`:
        ```python
        # ...
        except PaperlessInvalidTokenError as err:
            raise ConfigEntryError(  # Should be ConfigEntryAuthFailed
                translation_domain=DOMAIN,
                translation_key="invalid_api_key",
            ) from err
        except PaperlessInactiveOrDeletedError as err:
            raise ConfigEntryError(  # Should be ConfigEntryAuthFailed
                translation_domain=DOMAIN,
                translation_key="user_inactive_or_deleted",
            ) from err
        except PaperlessForbiddenError as err:
            raise ConfigEntryError(  # Potentially should be ConfigEntryAuthFailed
                translation_domain=DOMAIN,
                translation_key="forbidden",
            ) from err
        # ...
        ```
    *   In `PaperlessCoordinator._async_update_data()`:
        ```python
        # ...
        except PaperlessInvalidTokenError as err:
            raise ConfigEntryError( # Should be ConfigEntryAuthFailed
                translation_domain=DOMAIN,
                translation_key="invalid_api_key",
            ) from err
        except PaperlessInactiveOrDeletedError as err:
            raise ConfigEntryError( # Should be ConfigEntryAuthFailed
                translation_domain=DOMAIN,
                translation_key="user_inactive_or_deleted",
            ) from err
        # PaperlessForbiddenError raises UpdateFailed here, could also be ConfigEntryAuthFailed
        ```

Without these components, if a user's Paperless-ngx API key changes or becomes invalid, Home Assistant will not prompt them to re-enter the key. The integration will simply fail or enter an error state, requiring manual deletion and re-configuration.

## Suggestions

To make the `paperless_ngx` integration compliant with the `reauthentication-flow` rule, the following changes are recommended:

1.  **Modify `coordinator.py` to raise `ConfigEntryAuthFailed`:**
    Update the `PaperlessCoordinator` in `coordinator.py` to catch authentication-specific exceptions from the `pypaperless` library and re-raise them as `ConfigEntryAuthFailed`. This will signal Home Assistant to initiate the reauthentication flow.

    ```python
    # In homeassistant/components/paperless_ngx/coordinator.py
    # Add import:
    from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, ConfigEntryNotReady

    # ... inside PaperlessCoordinator class ...

    async def _async_setup(self) -> None:
        try:
            await self.api.initialize()
            await self.api.statistics()  # test permissions on api
        except PaperlessConnectionError as err:
            raise ConfigEntryNotReady(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
            ) from err
        except PaperlessInvalidTokenError as err:
            # MODIFIED: Raise ConfigEntryAuthFailed
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_api_key",
            ) from err
        except PaperlessInactiveOrDeletedError as err:
            # MODIFIED: Raise ConfigEntryAuthFailed
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="user_inactive_or_deleted",
            ) from err
        except PaperlessForbiddenError as err:
            # MODIFIED: Raise ConfigEntryAuthFailed (if this error implies a token issue)
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="forbidden",
            ) from err
        except InitializationError as err:
            raise ConfigEntryError( # This could remain ConfigEntryError if it's not auth related
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
            ) from err

    async def _async_update_data(self) -> Statistic:
        """Fetch data from API endpoint."""
        try:
            return await self.api.statistics()
        except PaperlessConnectionError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
            ) from err
        except PaperlessInvalidTokenError as err:
            # MODIFIED: Raise ConfigEntryAuthFailed
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_api_key",
            ) from err
        except PaperlessInactiveOrDeletedError as err:
            # MODIFIED: Raise ConfigEntryAuthFailed
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="user_inactive_or_deleted",
            ) from err
        except PaperlessForbiddenError as err:
            # MODIFIED: Raise ConfigEntryAuthFailed (if this error implies a token issue)
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="forbidden",
            ) from err
    ```

2.  **Implement the Reauthentication Flow in `config_flow.py`:**
    Add `async_step_reauth` and `async_step_reauth_confirm` methods to `PaperlessConfigFlow`.

    ```python
    # In homeassistant/components/paperless_ngx/config_flow.py
    # Add/ensure these imports:
    from collections.abc import Mapping # For entry_data type hint
    from homeassistant.config_entries import ConfigEntry, ConfigFlowResult # ConfigEntry for type hint

    # ... (keep existing imports like Paperless, exceptions, vol, CONF_API_KEY, CONF_URL, etc.)

    STEP_REAUTH_DATA_SCHEMA = vol.Schema(
        {
            vol.Required(CONF_API_KEY): str,
        }
    )

    class PaperlessConfigFlow(ConfigFlow, domain=DOMAIN):
        """Handle a config flow for Paperless-ngx."""

        # VERSION = 1 # If not already present, add and consider incrementing if schema changes

        _reauth_url: str | None = None # To store URL from original entry

        async def async_step_user(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            # ... (existing user step logic remains the same)
            # ...
            # Ensure this line is present or similar to prevent duplicate entries during initial setup
            # if user_input is not None:
            #    self._async_abort_entries_match(
            #        {
            #            CONF_URL: user_input[CONF_URL],
            #        }
            #    ) # Abort if URL already configured. API key can change.
            # Or, if unique ID is based on URL:
            # if user_input is not None:
            #     await self.async_set_unique_id(user_input[CONF_URL]) # Example, adjust as needed
            #     self._abort_if_unique_id_configured()

            # ... (rest of existing async_step_user)
            pass # Placeholder for existing code

        async def async_step_reauth(
            self, entry_data: Mapping[str, Any]
        ) -> ConfigFlowResult:
            """Perform reauthentication upon an API authentication error."""
            self._reauth_url = entry_data[CONF_URL]
            return await self.async_step_reauth_confirm()

        async def async_step_reauth_confirm(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            """Confirm reauthentication dialog."""
            errors: dict[str, str] = {}
            existing_entry = self.hass.config_entries.async_get_entry(
                self.context["entry_id"]
            )
            assert existing_entry # Should always exist here

            if user_input:
                client = Paperless(
                    self._reauth_url, # Use the stored URL
                    user_input[CONF_API_KEY],
                    session=async_get_clientsession(self.hass),
                )
                try:
                    await client.initialize()
                    await client.statistics()  # Verify the new token
                except PaperlessConnectionError:
                    errors["base"] = "cannot_connect" # Keep API_KEY field for error if more specific
                except PaperlessInvalidTokenError:
                    errors[CONF_API_KEY] = "invalid_api_key"
                except PaperlessInactiveOrDeletedError:
                    errors[CONF_API_KEY] = "user_inactive_or_deleted"
                except PaperlessForbiddenError:
                    errors[CONF_API_KEY] = "forbidden"
                except InitializationError: # Typically URL or connection related
                    errors["base"] = "cannot_connect"
                except Exception as err:  # noqa: BLE001
                    LOGGER.exception("Unexpected exception during reauth: %s", err)
                    errors["base"] = "unknown"
                else:
                    # Update the entry with the new API key
                    return self.async_update_reload_and_abort(
                        existing_entry,
                        data={**existing_entry.data, CONF_API_KEY: user_input[CONF_API_KEY]},
                    )

            return self.async_show_form(
                step_id="reauth_confirm",
                description_placeholders={"url": self._reauth_url},
                data_schema=STEP_REAUTH_DATA_SCHEMA,
                errors=errors,
            )
    ```

3.  **Add Translations for Reauthentication in `strings.json`:**
    Add entries for the reauthentication step in `homeassistant/components/paperless_ngx/strings.json`.

    ```json
    {
      "config": {
        "step": {
          "user": {
            // ... existing user step ...
          },
          "reauth_confirm": {
            "title": "Reauthenticate Paperless-ngx",
            "description": "The API key for your Paperless-ngx instance at `{url}` is no longer valid or has insufficient permissions. Please enter a new API key.",
            "data": {
              "api_key": "[%key:common::config_flow::data::api_key%]"
            }
          }
        },
        "error": {
          // ... existing errors ...
        },
        "abort": {
          // ... existing abort reasons ...
        }
      },
      // ... rest of the file ...
    }
    ```

By implementing these changes, the `paperless_ngx` integration will correctly handle authentication failures by prompting the user to update their API key through the Home Assistant UI, thus satisfying the `reauthentication-flow` rule and improving user experience.

_Created at 2025-05-27 13:06:56. Prompt tokens: 5978, Output tokens: 2849, Total tokens: 12757_
