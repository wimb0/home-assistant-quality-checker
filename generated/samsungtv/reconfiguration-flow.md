```markdown
# samsungtv: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **todo**                                       |

## Overview

The `reconfiguration-flow` rule requires integrations with configurable settings to provide a user-initiated flow to update those settings without needing to remove and re-add the integration. This rule is applicable to the `samsungtv` integration as it configures connection details like host, method, and potentially authentication tokens/PINs (`CONF_HOST`, `CONF_TOKEN`, `CONF_PIN`, `CONF_METHOD` in `config_flow.py`).

The provided code in `homeassistant/components/samsungtv/config_flow.py` includes steps for user-initiated configuration (`async_step_user`) and discovery-based flows (`async_step_ssdp`, `async_step_dhcp`, `async_step_zeroconf`, `async_step_confirm`), as well as steps for *re-authentication* (`async_step_reauth`, `async_step_reauth_confirm`, `async_step_reauth_confirm_encrypted`). The re-authentication flow is triggered automatically by the integration when an authentication failure is detected (e.g., lost token or PIN needed).

However, the integration currently lacks a general user-initiated "reconfigure" flow (typically implemented as `async_step_reconfigure`) that would allow a user to manually trigger a flow to change configuration settings like the host or connection method *before* or *without* an authentication error occurring. This is particularly useful if, for instance, the TV's IP address changes or a user wants to switch the connection method.

Therefore, while re-authentication is handled, a broader reconfiguration capability is missing according to this rule's requirements for a dedicated reconfigure step.

## Suggestions

To comply with the `reconfiguration-flow` rule, add an `async_step_reconfigure` method to the `SamsungTVConfigFlow` class in `homeassistant/components/samsungtv/config_flow.py`.

This step should allow the user to re-enter the primary configuration parameters, such as the host. It should then attempt to connect with the new details and potentially redirect to the appropriate pairing/authentication step (`async_step_pairing` or `async_step_encrypted_pairing`) if necessary (e.g., if the host changed or the method was updated).

Here is a possible structure for the `async_step_reconfigure` method, based on the rule's example and the existing `user` step logic:

```python
# In homeassistant/components/samsungtv/config_flow.py

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if not entry:
            return self.async_abort(reason="unknown")

        errors: dict[str, str] | None = None
        reconfigure_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST)): str,
            }
        )

        if user_input is not None:
            # Use the existing async_set_name_host_from_input to resolve hostname if needed
            if not await self._async_set_name_host_from_input(user_input):
                errors = {"base": "invalid_host"}
            else:
                # Update the temporary host and method based on existing entry,
                # then try creating a bridge. The bridge creation will attempt to
                # detect the correct method if the host changed and the method
                # needs re-evaluation.
                self._method = entry.data.get(CONF_METHOD)
                try:
                    await self._async_create_bridge() # This updates self._method and self._bridge based on connection attempt
                except AbortFlow as ex:
                    # Handle connection errors during reconfiguration attempt
                    errors = {"base": ex.reason}
                else:
                    # Connection successful, update entry with new host and potentially new method/port
                    data_updates = {CONF_HOST: self._host}
                    # If _async_create_bridge detected a different method/port, update it
                    if self._bridge.method != entry.data.get(CONF_METHOD):
                         data_updates[CONF_METHOD] = self._bridge.method
                    if self._bridge.port != entry.data.get(CONF_PORT):
                         data_updates[CONF_PORT] = self._bridge.port

                    # Attempt to get device info and unique id with the new connection
                    try:
                        await self._async_set_device_unique_id(raise_on_progress=False)
                         # Ensure unique id is set correctly in the context for update_reload_and_abort
                        self.context["unique_id"] = self._udn
                        # This will update unique_id and other discovery data if available
                        # It also handles conflicts/updates existing entries
                        self._async_update_and_abort_for_matching_unique_id()

                    except AbortFlow as ex:
                        # This could catch 'not_supported' or 'already_configured' if the unique_id changed
                        # If 'already_configured', it means the user reconfigured to a *different* TV.
                        # We should abort and let them add the other TV separately, or remove this one.
                        # If 'not_supported', the new host doesn't work.
                        errors = {"base": ex.reason}
                    except Exception:
                        # Catch any other unexpected errors during device info retrieval
                         LOGGER.exception("Error during device info update in reconfigure")
                         errors = {"base": "unknown"}

                    if not errors:
                        # If no errors, update the config entry and potentially proceed to pairing if needed
                        self.hass.config_entries.async_update_entry(entry, data={**entry.data, **data_updates})

                        if self._bridge.method == METHOD_ENCRYPTED_WEBSOCKET:
                             # If encrypted, we need to re-pair/get a new token/session ID
                             # Keep the updated data (host, method) but clear token/session_id to force pairing
                             updated_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
                             assert updated_entry
                             new_data = {**updated_entry.data}
                             new_data.pop(CONF_TOKEN, None)
                             new_data.pop(CONF_SESSION_ID, None)
                             self.hass.config_entries.async_update_entry(updated_entry, data=new_data)
                             # Redirect to encrypted pairing step
                             self.context["title_placeholders"] = {"device": self._title}
                             return await self.async_step_encrypted_pairing()
                        elif self._bridge.method == METHOD_LEGACY:
                             # Legacy doesn't require explicit pairing step in config flow,
                             # but might need re-acceptance popup.
                             # Just update and finish, the integration will handle it.
                             return self.async_update_reload_and_abort(entry)

                        # For standard websocket, just update and finish.
                        return self.async_update_reload_and_abort(entry)


        # Show the form for reconfigure
        self.context["title_placeholders"] = {"device": entry.title}
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(reconfigure_schema, user_input),
            errors=errors,
            description_placeholders={"device": entry.title},
        )

```

This suggestion outlines adding the `async_step_reconfigure` method, allowing the user to input a new host. It leverages existing logic to validate the host, attempt connection, detect the method, update the config entry, and potentially redirect to the pairing step if the encrypted method is used or re-authentication is required.

_Created at 2025-05-25 11:32:55. Prompt tokens: 30609, Output tokens: 1908, Total tokens: 33424_
