# nest: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-configure` rule requires that integrations test the connection to the device or service within the config flow and present an error to the user if the test fails, preventing the setup of a non-working integration.

This rule applies to the `nest` integration as it connects to the Google Nest cloud services (SDM API and Pub/Sub) and uses a config flow for setup.

The `nest` integration's config flow performs several checks at different stages:
1.  **OAuth2 Flow**: The standard OAuth2 flow implicitly tests the validity of Application Credentials (Client ID/Secret) and the user's ability to authenticate with Google and grant permissions for the specified Device Access Project ID.
2.  **Cloud Project ID and Pub/Sub Setup** (`async_step_pubsub_topic`, `async_step_pubsub_subscription`):
    *   It initializes an `AdminClient` using the obtained OAuth token and the user-provided Cloud Project ID.
    *   Calls like `self._admin_client.list_eligible_topics(...)`, `self._admin_client.create_topic(...)`, and `self._admin_client.create_subscription(...)` effectively test the Cloud Project ID, the token's permissions for Pub/Sub administration, and the ability to interact with the Pub/Sub API.
    *   If these calls raise an `ApiException`, the config flow correctly sets an error (e.g., `errors["base"] = "pubsub_api_error"`) and either re-shows the current form with the error or aborts the flow. This part adheres to the rule.

3.  **Smart Device Management (SDM) API Connection** (`async_step_pubsub_subscription`):
    *   After the Pub/Sub steps, the flow attempts to connect to the SDM API to verify it can list devices. This is done by calling `await subscriber.async_get_device_manager()`. This call uses the OAuth token and the Device Access Project ID.
    *   **This is where the integration does NOT fully follow the rule.**
        In `homeassistant/components/nest/config_flow.py`, within the `async_step_pubsub_subscription` method, if the `await subscriber.async_get_device_manager()` call raises an `ApiException` (e.g., due to an incorrect Device Access Project ID, SDM API not enabled, token issues, or no devices linked), the current implementation is:
        ```python
        # homeassistant/components/nest/config_flow.py
        # ...
                try:
                    device_manager = await subscriber.async_get_device_manager()
                except ApiException as err:
                    # Generating a user friendly home name is best effort
                    _LOGGER.debug("Error fetching structures: %s", err) # <--- Logs debug only
                else:
                    self._structure_config_title = generate_config_title(
                        device_manager.structures.values()
                    )
                return await self._async_finish() # <--- Proceeds to finish setup
        ```
        The code logs a debug message but then proceeds to call `await self._async_finish()`, which creates the config entry. This means the integration can be set up even if Home Assistant cannot communicate with the Nest SDM API to fetch devices, leading to a non-functional entry. The rule requires showing an error to the user and preventing setup in such a case.

Therefore, while parts of the connection testing are robust, the failure to handle errors from the primary SDM API device listing call and prevent configuration completion means the integration does not fully follow the `test-before-configure` rule.

## Suggestions

To make the `nest` integration compliant with the `test-before-configure` rule, the handling of `ApiException` during the `subscriber.async_get_device_manager()` call in `config_flow.py` needs to be improved.

1.  **Modify `async_step_pubsub_subscription` in `homeassistant/components/nest/config_flow.py`:**
    Update the `try...except` block for `await subscriber.async_get_device_manager()` as follows:

    ```python
    # In async_step_pubsub_subscription method:
    # ... (after Pub/Sub subscription creation logic) ...
    
            if not errors: # This 'errors' dict is from Pub/Sub checks
                self._data.update(user_input) # user_input contains the selected subscription
                                              # or CONF_SUBSCRIBER_ID_IMPORTED if applicable.
                                              # Ensure self._data[CONF_SUBSCRIPTION_NAME] is correctly set.
                
                # If a new subscription was created, user_input might be {'subscription_name': 'newly_created_name'}
                # Ensure self._data[CONF_SUBSCRIPTION_NAME] reflects the actual subscription name to be used.
                # Example adjustment if subscription_name was dynamically generated:
                # if subscription_name == CREATE_NEW_SUBSCRIPTION_KEY:
                #    self._data[CONF_SUBSCRIPTION_NAME] = newly_generated_subscription_name 
                # else:
                #    self._data[CONF_SUBSCRIPTION_NAME] = user_input[CONF_SUBSCRIPTION_NAME]

                subscriber = api.new_subscriber_with_token(
                    self.hass,
                    self._data["token"]["access_token"],
                    self._data[CONF_PROJECT_ID], # Device Access Project ID
                    self._data[CONF_SUBSCRIPTION_NAME], # The actual subscription name
                )
                try:
                    device_manager = await subscriber.async_get_device_manager()
                except ApiException as err:
                    _LOGGER.error("Failed to connect to Nest SDM API to list devices/structures: %s", err)
                    errors["base"] = "cannot_connect_sdm"  # New error key
                except Exception:  # noqa: BLE001
                    _LOGGER.exception("Unexpected error connecting to Nest SDM API")
                    errors["base"] = "unknown_sdm_error" # New error key
                else:
                    # Successfully connected and got device manager
                    self._structure_config_title = generate_config_title(
                        device_manager.structures.values()
                    )
                    # Only finish if successful
                    return await self._async_finish()

        # This part is reached if user_input was None (initial display of form) 
        # OR if errors occurred in Pub/Sub setup OR SDM connection test.
        # The form for pubsub_subscription will be re-shown with the errors.
        # ... (schema for pubsub_subscription) ...
        return self.async_show_form(
            step_id="pubsub_subscription",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SUBSCRIPTION_NAME,
                        default=next(iter(subscriptions)), # existing logic for options
                    ): SelectSelector(...) # existing logic for selector
                }
            ),
            description_placeholders={
                "topic": self._data[CONF_TOPIC_NAME],
                "more_info_url": MORE_INFO_URL,
            },
            errors=errors, # This will now include "cannot_connect_sdm" if that error occurred
        )
    ```

2.  **Add new error keys to `homeassistant/components/nest/strings.json`:**
    Under the `config.error` section, add translations for the new error keys:
    ```json
    {
      "config": {
        "error": {
          // ... existing errors ...
          "cannot_connect_sdm": "Failed to connect to the Smart Device Management API. Please verify your Device Access Project ID, ensure the SDM API is enabled in Google Cloud Console, and that devices are correctly linked to your account.",
          "unknown_sdm_error": "An unknown error occurred while trying to connect to the Smart Device Management API. Check logs for details."
        },
        // ... rest of the file ...
      }
    }
    ```

**Why these changes satisfy the rule:**
*   The suggested code modification ensures that if `subscriber.async_get_device_manager()` (the test call to the SDM API) fails, an appropriate error message (`cannot_connect_sdm` or `unknown_sdm_error`) is added to the `errors` dictionary.
*   Crucially, `await self._async_finish()` (which calls `self.async_create_entry`) is *not* called if an exception occurs during the SDM API test.
*   Instead, the `async_show_form` for the `pubsub_subscription` step is called again, displaying the error message to the user.
*   This prevents the creation of a config entry if the core functionality (communicating with the SDM API to get devices) cannot be established, directly addressing the requirements of the `test-before-configure` rule.

_Created at 2025-05-28 22:52:03. Prompt tokens: 32569, Output tokens: 2113, Total tokens: 40022_
