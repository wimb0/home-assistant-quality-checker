# music_assistant: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `reconfiguration-flow` rule requires integrations to implement an `async_step_reconfigure` method in their config flow. This allows users to modify settings of an already configured integration (e.g., IP address, API key) without needing to remove and re-add it.

This rule applies to the `music_assistant` integration because:
1.  It uses a config flow (`"config_flow": true` in `manifest.json`).
2.  The config flow involves a configurable setting: the URL of the Music Assistant server (`CONF_URL` in `config_flow.py`). This URL might change if the server's IP address or port changes, making reconfiguration necessary.

The `music_assistant` integration currently does **not** follow this rule.
Upon inspection of its `config_flow.py` file, the `MusicAssistantConfigFlow` class defines `async_step_user` and `async_step_zeroconf`, but it does not implement the required `async_step_reconfigure` method.

While the `async_step_user` and `async_step_zeroconf` methods use `self._abort_if_unique_id_configured(updates={CONF_URL: self.server_info.base_url}, reload_on_update=True)`, which can update an existing entry if a user tries to add it again or if it's rediscovered, this is not the dedicated reconfiguration flow triggered by the "RECONFIGURE" option in the Home Assistant UI for an existing config entry. The rule expects an explicit `async_step_reconfigure` entry point for a user-friendly way to modify existing settings.

## Suggestions

To make the `music_assistant` integration compliant with the `reconfiguration-flow` rule, an `async_step_reconfigure` method should be added to the `MusicAssistantConfigFlow` class in `homeassistant/components/music_assistant/config_flow.py`.

This method should:
1.  Be triggered when a user initiates a reconfigure action on an existing Music Assistant config entry.
2.  Present a form to the user, pre-filled with the current server URL.
3.  Allow the user to input a new URL.
4.  Validate the new URL by attempting to connect and fetch server information (similar to `async_step_user`).
5.  Crucially, verify that the `server_id` obtained from the new URL matches the `unique_id` of the existing config entry. This prevents accidentally reconfiguring the entry to point to a completely different Music Assistant server instance. The rule's example uses `self._abort_if_unique_id_mismatch()`.
6.  If validation and the unique ID check pass, update the config entry's data with the new URL and reload the integration using `self.async_update_reload_and_abort()`.

Here's an example snippet of how `async_step_reconfigure` could be implemented:

```python
# In homeassistant/components/music_assistant/config_flow.py

# ... (other imports)
# Ensure CONF_URL is imported or defined
# from homeassistant.const import CONF_URL

class MusicAssistantConfigFlow(ConfigFlow, domain=DOMAIN):
    # ... (existing methods __init__, async_step_user, async_step_zeroconf, etc.)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the Music Assistant server URL."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if not entry:
            # Should not happen if the flow is initiated correctly
            return self.async_abort(reason="unknown_entry")

        errors: dict[str, str] = {}

        if user_input is not None:
            new_url = user_input[CONF_URL]
            try:
                # Validate the new URL and get server_info
                # Re-use or adapt the get_server_info logic from async_step_user
                server_info = await get_server_info(self.hass, new_url)

                # Set the unique_id based on the new server_info for comparison
                await self.async_set_unique_id(server_info.server_id)
                # Abort if the new server_id does not match the existing entry's unique_id
                # self.context["unique_id"] holds the unique_id of the entry being reconfigured.
                self._abort_if_unique_id_mismatch(reason="cannot_change_server_instance") # Add "cannot_change_server_instance" to strings.json

                # If successful and unique_id matches, update and reload
                return self.async_update_reload_and_abort(
                    entry,
                    data={CONF_URL: server_info.base_url},
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidServerVersion:
                errors["base"] = "invalid_server_version"
            except MusicAssistantClientException:
                LOGGER.exception("Unexpected exception during reconfiguration")
                errors["base"] = "unknown"
            # Do not catch AbortFlow from _abort_if_unique_id_mismatch here

        # Show the form, pre-filled with the current URL
        current_url = entry.data.get(CONF_URL, DEFAULT_URL)
        data_schema = vol.Schema({
            vol.Required(CONF_URL, default=current_url): str,
        })

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"name": entry.title}, # Optional: customize description
        )

```

**Explanation of Changes:**
*   The `async_step_reconfigure` method is added.
*   It retrieves the current `ConfigEntry` to pre-fill the form with the existing URL.
*   When the user submits a new URL, it attempts to connect using `get_server_info`.
*   `await self.async_set_unique_id(server_info.server_id)` sets the unique ID for the *current flow execution* based on the *new* server info.
*   `self._abort_if_unique_id_mismatch(reason="cannot_change_server_instance")` compares this newly set unique ID with the `unique_id` of the original config entry (`self.context["unique_id"]`). If they differ, it aborts, preventing the user from accidentally pointing the HA config entry to a different Music Assistant server. A corresponding error message key (`cannot_change_server_instance`) would need to be added to `strings.json`.
*   If all checks pass, `self.async_update_reload_and_abort()` updates the `CONF_URL` in the config entry's data and triggers a reload of the integration.

Implementing this `async_step_reconfigure` flow would make the integration compliant with the rule and improve the user experience for updating the server URL.

_Created at 2025-05-14 13:45:13. Prompt tokens: 30590, Output tokens: 1727, Total tokens: 35704_
