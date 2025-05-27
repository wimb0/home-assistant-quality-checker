# paperless_ngx: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [paperless_ngx](https://www.home-assistant.io/integrations/paperless_ngx/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `repair-issues` rule mandates that integrations should use Home Assistant's repair issue system or repair flows when user intervention is needed to resolve a problem. This provides a user-friendly way to inform users about actionable issues.

This rule applies to the `paperless_ngx` integration because it communicates with an external Paperless-ngx service, which can lead to various user-fixable problems such as authentication failures, connection issues, or permission errors.

The `paperless_ngx` integration currently does **not fully** follow this rule.

1.  **Authentication Errors:**
    In `coordinator.py`, errors like `PaperlessInvalidTokenError` and `PaperlessInactiveOrDeletedError` are caught and re-raised as `ConfigEntryError` with specific translation keys (e.g., `invalid_api_key`, `user_inactive_or_deleted`).
    ```python
    # homeassistant/components/paperless_ngx/coordinator.py
    # In _async_setup and _async_update_data
    # ...
    except PaperlessInvalidTokenError as err:
        raise ConfigEntryError(  # Or ConfigEntryAuthFailed would be more specific
            translation_domain=DOMAIN,
            translation_key="invalid_api_key",
        ) from err
    except PaperlessInactiveOrDeletedError as err:
        raise ConfigEntryError( # Or ConfigEntryAuthFailed
            translation_domain=DOMAIN,
            translation_key="user_inactive_or_deleted",
        ) from err
    # ...
    ```
    If these `ConfigEntryError` instances are interpreted by Home Assistant core as authentication failures (which is more robustly achieved by raising `ConfigEntryAuthFailed`), Home Assistant will typically automatically create a repair issue and offer a re-authentication flow. This partially addresses the rule for these specific errors by leveraging a "repair flow".

2.  **Connection and Permission Errors (Runtime):**
    During runtime data updates (`PaperlessCoordinator._async_update_data`), other user-fixable errors like `PaperlessConnectionError` (e.g., Paperless-ngx service is down or URL changed) or `PaperlessForbiddenError` (e.g., API token is valid but lacks permissions) are caught and result in `UpdateFailed` being raised.
    ```python
    # homeassistant/components/paperless_ngx/coordinator.py
    # In _async_update_data
    # ...
    except PaperlessConnectionError as err:
        raise UpdateFailed(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
        ) from err
    except PaperlessForbiddenError as err:
        raise UpdateFailed(
            translation_domain=DOMAIN,
            translation_key="forbidden",
        ) from err
    # ...
    ```
    Raising `UpdateFailed` logs an error and causes entities to become unavailable or not update, but it does *not* create a persistent, user-facing Repair Issue in the Home Assistant UI. The user is not clearly guided on what is wrong or how to fix it via the Repairs dashboard. These are scenarios where `ir.async_create_issue` should be used to inform the user, as per the rule's intent and example (which shows creating a repair issue for an "outdated_version" which is user-fixable but not an auth issue).

The integration does not currently import `homeassistant.helpers.issue_registry as ir` or make calls to `ir.async_create_issue` for these non-authentication runtime errors that require user intervention.

## Suggestions

To make the `paperless_ngx` integration compliant with the `repair-issues` rule, consider the following changes:

1.  **Use `ConfigEntryAuthFailed` for Authentication Errors:**
    For clearer signaling to Home Assistant core that an error is specifically an authentication failure (which robustly triggers re-auth flows and associated repair issues), modify the exception handling in `coordinator.py` for `PaperlessInvalidTokenError` and `PaperlessInactiveOrDeletedError` to raise `homeassistant.exceptions.ConfigEntryAuthFailed`.

    ```python
    # homeassistant/components/paperless_ngx/coordinator.py
    from homeassistant.exceptions import (
        ConfigEntryAuthFailed,  # Import this
        ConfigEntryError,
        ConfigEntryNotReady,
    )
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
    # ...

    class PaperlessCoordinator(DataUpdateCoordinator[Statistic]):
        # ...
        async def _async_setup(self) -> None:
            try:
                # ...
            except PaperlessInvalidTokenError as err:
                raise ConfigEntryAuthFailed(  # Changed from ConfigEntryError
                    translation_domain=DOMAIN,
                    translation_key="invalid_api_key",
                ) from err
            except PaperlessInactiveOrDeletedError as err:
                raise ConfigEntryAuthFailed(  # Changed from ConfigEntryError
                    translation_domain=DOMAIN,
                    translation_key="user_inactive_or_deleted",
                ) from err
            # ... (other exceptions remain as ConfigEntryError or ConfigEntryNotReady)

        async def _async_update_data(self) -> Statistic:
            try:
                # ...
            except PaperlessInvalidTokenError as err:
                raise ConfigEntryAuthFailed(  # Changed from ConfigEntryError
                    translation_domain=DOMAIN,
                    translation_key="invalid_api_key",
                ) from err
            except PaperlessInactiveOrDeletedError as err:
                raise ConfigEntryAuthFailed(  # Changed from ConfigEntryError
                    translation_domain=DOMAIN,
                    translation_key="user_inactive_or_deleted",
                ) from err
            # ...
    ```
    This change ensures that Home Assistant's standard re-authentication repair flow is reliably triggered.

2.  **Create Repair Issues for Runtime Connection/Permission Errors:**
    For errors like `PaperlessConnectionError` and `PaperlessForbiddenError` encountered during `_async_update_data`, use `homeassistant.helpers.issue_registry.async_create_issue` to inform the user.

    *   Import the issue registry:
        ```python
        # homeassistant/components/paperless_ngx/coordinator.py
        import homeassistant.helpers.issue_registry as ir
        ```

    *   Modify `_async_update_data` to create issues:
        ```python
        # homeassistant/components/paperless_ngx/coordinator.py
        async def _async_update_data(self) -> Statistic:
            """Fetch data from API endpoint."""
            try:
                stats = await self.api.statistics()
                # Clear any previous non-auth issues if successful
                ir.async_delete_issue(self.hass, DOMAIN, "connection_error")
                ir.async_delete_issue(self.hass, DOMAIN, "forbidden_error")
                return stats
            except PaperlessConnectionError as err:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "connection_error",
                    is_fixable=False,
                    is_persistent=False, # Or True if you want it to persist across restarts until resolved
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="issue_connection_error",
                    translation_placeholders={"url": str(self.api.base_url)},
                )
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="cannot_connect", # This existing key can be reused for UpdateFailed message
                ) from err
            except PaperlessForbiddenError as err:
                # Assuming this means the token is valid but lacks permissions
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "forbidden_error",
                    is_fixable=False,
                    is_persistent=False,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="issue_forbidden_error",
                )
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="forbidden", # This existing key can be reused for UpdateFailed message
                ) from err
            except PaperlessInvalidTokenError as err: # Keep or change to ConfigEntryAuthFailed as per suggestion 1
                # If using ConfigEntryAuthFailed, HA Core handles the repair issue for re-auth
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="invalid_api_key",
                ) from err
            except PaperlessInactiveOrDeletedError as err: # Keep or change to ConfigEntryAuthFailed
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="user_inactive_or_deleted",
                ) from err
        ```

3.  **Add Translation Strings for New Repair Issues:**
    In `homeassistant/components/paperless_ngx/strings.json`, add entries for the new repair issues under an `issues` key:
    ```json
    {
      "config": { ... },
      "entity": { ... },
      "exceptions": { ... },
      "issues": {
        "connection_error": {
          "title": "Cannot Connect to Paperless-ngx",
          "description": "Home Assistant is unable to connect to your Paperless-ngx instance at `{url}`. Please verify that the URL is correct in the integration configuration, Paperless-ngx is running, and your network allows connection. If the URL or service details have changed, you may need to re-configure the integration."
        },
        "forbidden_error": {
          "title": "Paperless-ngx API Access Forbidden",
          "description": "The API token used for Paperless-ngx integration has insufficient permissions to access required data or has been revoked. Please check the API token's permissions within your Paperless-ngx instance or generate a new token with appropriate access and re-configure the integration."
        }
      }
    }
    ```

These changes will ensure that users are proactively informed about actionable problems through the Home Assistant Repairs dashboard, improving the user experience and adherence to the `repair-issues` quality scale rule.

_Created at 2025-05-27 13:10:48. Prompt tokens: 5418, Output tokens: 2376, Total tokens: 15064_
