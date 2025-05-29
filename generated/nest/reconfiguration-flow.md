# nest: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `reconfiguration-flow` rule requires integrations to provide a way for users to update their configuration settings without needing to remove and re-add the integration. This is particularly useful for settings that might change post-setup, such as Pub/Sub details in the case of the Nest integration.

The Nest integration's configuration involves several pieces of data stored in the config entry:
*   `CONF_CLIENT_ID` and `CONF_CLIENT_SECRET` (via Application Credentials).
*   `CONF_CLOUD_PROJECT_ID`: The Google Cloud Project ID.
*   `CONF_PROJECT_ID`: The Nest Device Access Project ID. This is also used as the `unique_id` for the config entry.
*   `CONF_TOPIC_NAME`: The Google Cloud Pub/Sub topic for device events.
*   `CONF_SUBSCRIPTION_NAME`: The Google Cloud Pub/Sub subscription.
*   OAuth tokens for API access.

Authentication-related issues (like expired OAuth tokens) are handled by the re-authentication flow, which Nest implements via `async_step_reauth` in `homeassistant/components/nest/config_flow.py`.

However, the `CONF_TOPIC_NAME` and `CONF_SUBSCRIPTION_NAME` are settings that a user might need to change if they modify their Google Cloud Pub/Sub setup (e.g., reorganizing topics, changing project structures related to Pub/Sub, or needing to point to a different, pre-existing subscription). Currently, to change these Pub/Sub settings, a user would have to delete the Nest integration and set it up again, including the OAuth authorization process. This is cumbersome.

The rule applies because the Nest integration stores these configurable Pub/Sub settings in its config entry, and these are settings a user might reasonably want to change after the initial setup. The integration currently does **not** implement an `async_step_reconfigure` method in its `config_flow.py` to allow for modification of these settings.

The `CONF_PROJECT_ID` is the unique ID for the config entry and generally should not be changed during a reconfiguration of an existing entry. Similarly, `CONF_CLOUD_PROJECT_ID` is a fundamental setup parameter. A reconfiguration flow should primarily focus on the Pub/Sub aspects.

## Suggestions

To comply with the `reconfiguration-flow` rule, the Nest integration should implement an `async_step_reconfigure` method in `homeassistant/components/nest/config_flow.py`. This flow should allow users to modify the `CONF_TOPIC_NAME` and `CONF_SUBSCRIPTION_NAME` for an existing configuration entry.

Here's a suggested approach:

1.  **Add `async_step_reconfigure` to `NestFlowHandler`:**
    This method will be the entry point for the reconfiguration flow. It should be accessible from the integrations page for an existing Nest config entry.

2.  **Initialize with existing configuration:**
    The flow should load the current `CONF_PROJECT_ID`, `CONF_CLOUD_PROJECT_ID`, `CONF_TOPIC_NAME`, `CONF_SUBSCRIPTION_NAME`, and OAuth token data from the existing config entry. The Project IDs should generally be treated as fixed for this flow.

3.  **Allow modification of Pub/Sub settings:**
    The user should be able to specify new values for `CONF_TOPIC_NAME` and `CONF_SUBSCRIPTION_NAME`. This could be achieved in a few ways:
    *   **Simple Input:** A form where users directly input the new full topic and subscription names. This is simpler to implement but requires users to know the exact names.
    *   **Interactive Selection/Creation:** Reuse or adapt the logic from `async_step_pubsub_topic` and `async_step_pubsub_subscription`. This would involve:
        *   Creating new reconfigure-specific steps (e.g., `async_step_reconfigure_pubsub_topic`, `async_step_reconfigure_pubsub_subscription`).
        *   These steps would use the existing `CONF_CLOUD_PROJECT_ID` and OAuth token to list eligible topics/subscriptions or guide through creating new ones, similar to the initial setup.
        *   Forms should be pre-filled with current values.

4.  **Validate new Pub/Sub settings:**
    Before saving, the new Pub/Sub topic and subscription must be validated using the `AdminClient` (obtained via `api.new_pubsub_admin_client` with the existing OAuth token and `CONF_CLOUD_PROJECT_ID`). This includes:
    *   Verifying the topic exists and is accessible.
    *   Verifying the subscription exists, is linked to the (potentially new) topic, and is accessible by the SDM service.
    *   Handling potential errors (e.g., `ApiException`) and showing them to the user.
    *   If a user selects/creates a subscription they manage themselves, the `CONF_SUBSCRIBER_ID_IMPORTED` flag should be appropriately set/cleared.

5.  **Update and reload the config entry:**
    If validation is successful, update the config entry with the new (or existing) `CONF_TOPIC_NAME` and `CONF_SUBSCRIPTION_NAME`. Use `self.async_update_reload_and_abort()` to save the changes and trigger a reload of the integration.

**Conceptual Code Snippet:**

```python
# In homeassistant/components/nest/config_flow.py

class NestFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    # ... existing methods ...

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of Pub/Sub settings."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        # Ensure entry is not None
        if entry is None:
            return self.async_abort(reason="unknown_entry")

        errors: dict[str, str] = {}
        current_entry_data = dict(entry.data)

        if user_input is not None:
            # This example assumes direct input of new topic/subscription names.
            # A more robust implementation would involve steps similar to initial setup
            # for selecting/creating topics and subscriptions.
            new_topic_name = user_input[CONF_TOPIC_NAME]
            new_subscription_name = user_input[CONF_SUBSCRIPTION_NAME]

            try:
                # --- Begin Validation Section (Simplified) ---
                # Re-use or adapt validation logic from initial setup.
                # This requires an AdminClient and existing OAuth token.
                access_token = current_entry_data["token"]["access_token"]
                admin_client = api.new_pubsub_admin_client(
                    self.hass,
                    access_token=access_token,
                    cloud_project_id=current_entry_data[CONF_CLOUD_PROJECT_ID],
                )

                # Example: Validate topic (actual validation is more complex)
                await admin_client.get_topic(new_topic_name)
                # Example: Validate subscription (actual validation is more complex)
                await admin_client.get_subscription(new_subscription_name)
                # TODO: Add full validation logic, ensuring subscription matches topic, etc.
                # --- End Validation Section ---

                updated_pubsub_data = {
                    CONF_TOPIC_NAME: new_topic_name,
                    CONF_SUBSCRIPTION_NAME: new_subscription_name,
                    # Handle CONF_SUBSCRIBER_ID_IMPORTED if user provides an existing subscription
                }
                
                new_data_for_entry = {**current_entry_data, **updated_pubsub_data}

                _LOGGER.info("Reconfiguring Nest entry %s with new Pub/Sub settings", entry.entry_id)
                return self.async_update_reload_and_abort(
                    entry,
                    data=new_data_for_entry,
                )
            except ApiException as err:
                _LOGGER.error("Error during Pub/Sub reconfiguration: %s", err)
                errors["base"] = "pubsub_api_error" # Use a more specific error if possible
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during Nest reconfiguration")
                errors["base"] = "unknown"
        
        # Pre-fill the form with current values
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_TOPIC_NAME, default=current_entry_data.get(CONF_TOPIC_NAME, "")
                ): str,
                vol.Required(
                    CONF_SUBSCRIPTION_NAME,
                    default=current_entry_data.get(CONF_SUBSCRIPTION_NAME, ""),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "project_id": current_entry_data[CONF_PROJECT_ID],
                "cloud_project_id": current_entry_data[CONF_CLOUD_PROJECT_ID],
                # Add link to documentation or relevant Google Cloud console pages
            },
        )

    # If choosing a more interactive approach, add helper steps:
    # async def async_step_reconfigure_pubsub_topic(self, user_input=None): ...
    # async def async_step_reconfigure_pubsub_subscription(self, user_input=None): ...
```

By implementing such a flow, users can update their Nest integration's Pub/Sub configuration without the friction of a full removal and re-setup, improving the user experience and fulfilling the requirements of the `reconfiguration-flow` rule.

_Created at 2025-05-28 23:14:38. Prompt tokens: 32835, Output tokens: 2327, Total tokens: 41146_
