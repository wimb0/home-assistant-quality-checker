# overkiz: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **todo**                                                                 |

## Overview

The `reconfiguration-flow` rule requires integrations to implement an `async_step_reconfigure` method in their `config_flow.py`. This allows users to modify the configuration of an already set-up integration (e.g., update credentials, change a host IP) without needing to delete and re-add the integration.

This rule applies to the `overkiz` integration because:
1.  It has a config flow (`"config_flow": true` in `manifest.json`).
2.  The config flow involves settings that a user might need to change post-setup, such as:
    *   For cloud API: `CONF_USERNAME`, `CONF_PASSWORD`.
    *   For local API: `CONF_HOST`, `CONF_TOKEN`, `CONF_VERIFY_SSL`.

Currently, the `overkiz` integration's `config_flow.py` (specifically in `homeassistant/components/overkiz/config_flow.py`) **does not implement** the `async_step_reconfigure` method.

While it has an `async_step_reauth` flow that allows updating credentials if authentication fails, this does not fully satisfy the `reconfiguration-flow` rule. A reconfigure flow should be user-initiated even when the integration is working correctly, allowing changes to any pertinent configuration parameters (like host IP or SSL verification settings for the local API), not just credentials due to an auth failure.

Without `async_step_reconfigure`, users cannot proactively change settings like the `CONF_HOST` for a local API setup or `CONF_VERIFY_SSL` unless an authentication error occurs or they delete and re-add the integration.

## Suggestions

To make the `overkiz` integration compliant with the `reconfiguration-flow` rule, implement the `async_step_reconfigure` method in `homeassistant/components/overkiz/config_flow.py`.

This method should:
1.  Retrieve the existing config entry.
2.  Determine the API type (cloud or local) from the entry's data to present the correct form.
3.  Show a form pre-filled with the current configurable values (e.g., username for cloud, host for local). Passwords and tokens should not be pre-filled for security.
4.  Upon submission, validate the new input using a similar mechanism to the initial setup (e.g., reusing `async_validate_input`).
5.  Ensure that the reconfiguration does not inadvertently change the integration to a different gateway/account. This means the `unique_id` derived from the new settings must match the `unique_id` of the entry being reconfigured. An abort should occur if they mismatch (e.g., using `self.async_abort(reason="reauth_wrong_account")`).
6.  Additionally, use `self._abort_if_unique_id_mismatch()` to ensure the (now confirmed same as original) unique ID doesn't clash with another *different* entry.
7.  If validation is successful and the unique ID matches, update the config entry using `self.async_update_reload_and_abort(entry, data=validated_data)`.

Here's an example implementation for `async_step_reconfigure`:

```python
# homeassistant/components/overkiz/config_flow.py

# ... other imports ...
from pyoverkiz.enums import APIType, Server # Ensure APIType and Server are imported
from homeassistant.config_entries import ConfigEntry # Ensure ConfigEntry is imported

# ... inside OverkizConfigFlow class ...

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user to reconfigure an entry."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if not entry:
            # Should not happen if the flow is initiated from an existing entry
            return self.async_abort(reason="unknown_entry")

        errors: dict[str, str] = {}
        
        # Determine API type and hub from existing entry to show the correct form and for validation
        api_type = entry.data.get(CONF_API_TYPE, APIType.CLOUD)
        current_hub = entry.data[CONF_HUB]

        if user_input:
            # Create the full data set for validation by merging existing data with user's new input.
            # User input only contains fields from the reconfigure form.
            data_for_validation = {**entry.data, **user_input}
            # Ensure hub and api_type are fixed from the original entry for validation logic.
            data_for_validation[CONF_HUB] = current_hub
            data_for_validation[CONF_API_TYPE] = api_type

            # Set instance variables required by async_validate_input
            self._api_type = api_type
            self._server = current_hub # Used by async_validate_input for cloud API client
            if api_type == APIType.LOCAL:
                # For local API, _verify_ssl needs to be set. It comes from user_input or defaults from entry.
                self._verify_ssl = data_for_validation.get(CONF_VERIFY_SSL, entry.data.get(CONF_VERIFY_SSL, True))

            try:
                # async_validate_input will:
                # 1. Create a client based on data_for_validation.
                # 2. Attempt to login with new credentials/settings.
                # 3. Retrieve gateway(s) and call `await self.async_set_unique_id(gateway.id, raise_on_progress=False)`.
                #    This updates `self.unique_id` with the unique ID derived from the new settings.
                # It returns the full, validated data dictionary.
                validated_data = await self.async_validate_input(data_for_validation)

            # Handle exceptions similar to how they are handled in async_step_cloud / async_step_local
            except TooManyRequestsException:
                errors["base"] = "too_many_requests"
            except (BadCredentialsException, NotSuchTokenException, NotAuthenticatedException) as e:
                if api_type == APIType.CLOUD and current_hub in {
                    Server.ATLANTIC_COZYTOUCH, Server.SAUTER_COZYTOUCH, Server.THERMOR_COZYTOUCH
                } and not isinstance(e, CozyTouchBadCredentialsException):
                    errors["base"] = "unsupported_hardware"
                    # self.context["title_placeholders"] could add unsupported_device if needed for form
                else:
                    errors["base"] = "invalid_auth"
            except UnknownUserException: # Cloud only
                errors["base"] = "unsupported_hardware"
                # self.context["title_placeholders"] could add unsupported_device
            except ClientConnectorCertificateError: # Local only
                errors["base"] = "certificate_verify_failed"
            except (TimeoutError, ClientError):
                errors["base"] = "cannot_connect"
            except MaintenanceException:
                errors["base"] = "server_in_maintenance"
            except TooManyAttemptsBannedException:
                errors["base"] = "too_many_attempts"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unknown error during reconfiguration validation")
                errors["base"] = "unknown"
            else:
                # Critical check: The unique_id derived from the new settings must match the
                # unique_id of the entry being reconfigured.
                if self.unique_id != entry.unique_id:
                    return self.async_abort(reason="reauth_wrong_account")

                # This checks if the unique_id (now confirmed to be the same as original)
                # conflicts with any *other* existing entries.
                # This uses self.unique_id internally and excludes the current entry by context.
                self._abort_if_unique_id_mismatch(reason="reauth_wrong_account")
                
                # Update the entry with the validated data.
                return self.async_update_reload_and_abort(
                    entry, data=validated_data
                )
        
        # Determine data schema for the form based on the API type of the existing entry.
        # Pre-fill with existing values, but not password/token.
        if api_type == APIType.LOCAL:
            schema_fields = {
                vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST)): str,
                vol.Required(CONF_TOKEN): str, # Token is always required, not pre-filled
                vol.Required(CONF_VERIFY_SSL, default=entry.data.get(CONF_VERIFY_SSL, True)): bool,
            }
        else: # APIType.CLOUD
            schema_fields = {
                vol.Required(CONF_USERNAME, default=entry.data.get(CONF_USERNAME)): str,
                vol.Required(CONF_PASSWORD): str, # Password is always required, not pre-filled
            }
        
        data_schema = vol.Schema(schema_fields)

        return self.async_show_form(
            step_id="reconfigure", # This is the step_id for the reconfigure form submission
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"gateway_id": entry.unique_id or ""} # Show current gateway ID
        )

```

**Explanation of Changes:**
*   The `async_step_reconfigure` method is added.
*   It fetches the current `ConfigEntry` to pre-fill forms and for final validation.
*   It determines the `api_type` (cloud/local) from the existing entry to display the appropriate form fields (`CONF_USERNAME`/`CONF_PASSWORD` for cloud, `CONF_HOST`/`CONF_TOKEN`/`CONF_VERIFY_SSL` for local).
*   The `CONF_HUB` is considered non-reconfigurable as changing it fundamentally alters the target server and likely the unique ID; it's part of the initial setup.
*   It reuses `self.async_validate_input()` for validating the new credentials/settings. Instance variables `self._api_type`, `self._server`, and `self._verify_ssl` are set before calling `async_validate_input`.
*   A crucial check `if self.unique_id != entry.unique_id:` ensures the user is reconfiguring the same gateway/account. `self.unique_id` is updated by `async_validate_input`.
*   `self._abort_if_unique_id_mismatch()` is called to prevent conflicts with other entries.
*   If successful, `self.async_update_reload_and_abort(entry, data=validated_data)` updates the configuration entry.
*   Error handling is included, mirroring the patterns in the existing `async_step_cloud` and `async_step_local` methods.

By implementing this, `overkiz` will allow users to proactively modify their configuration details, enhancing usability and aligning with Home Assistant's integration quality standards.

_Created at 2025-05-28 12:43:53. Prompt tokens: 87475, Output tokens: 2646, Total tokens: 100702_
