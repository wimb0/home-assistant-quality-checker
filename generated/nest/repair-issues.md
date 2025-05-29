# nest: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `repair-issues` rule requires integrations to use repair issues and repair flows to notify users about actionable problems and guide them towards a resolution.

The `nest` integration interacts with the Google Nest Smart Device Management (SDM) API, which involves cloud authentication, Pub/Sub messaging for real-time updates, and specific API configurations. This setup can lead to various user-actionable issues such as authentication failures, misconfigurations in the Google Cloud Project (e.g., Pub/Sub topic/subscription issues, API enablement), or changes in device structure recognized by the SDM API.

The rule applies to the `nest` integration.

The integration currently follows this rule partially:
*   **Authentication Failures:** It correctly uses `ConfigEntryAuthFailed` (e.g., in `__init__.py` lines 194, 218) when an authentication error occurs (e.g., `AuthException`, certain `ClientResponseError`s). This typically triggers a re-authentication flow managed by Home Assistant, which is a form of repair.

However, the integration does not fully follow the rule because it does not utilize `homeassistant.helpers.issue_registry` (commonly aliased as `ir`) to create repair issues for other types of user-actionable problems. These include:

1.  **Post-setup Configuration Errors:**
    *   In `__init__.py`, when `async_setup_entry` encounters a `ConfigurationException` (line 223), it logs an error and returns `False`, causing the setup to fail. This could be due to an invalid Pub/Sub setup or other SDM project misconfigurations that the user can fix in their Google Cloud Console. A repair issue would be more user-friendly, guiding the user on what to check.
    *   Similarly, `SubscriberException` (line 226) or `ApiException` (line 231) can arise from user-fixable issues in the Pub/Sub or SDM API setup (e.g., deleted subscription, insufficient permissions, API not enabled) that are not currently translated into specific repair issues.

2.  **Device Structure Changes:**
    *   In `__init__.py`, line 135, when an `event_message.relation_update` is received (indicating devices or homes have changed in the Nest backend), the integration only logs: `"Devices or homes have changed; Need reload to take effect"`. This is a prime candidate for a repair issue with `is_fixable=True` and a simple repair flow to reload the config entry, making it directly actionable by the user from the UI.

No instances of `ir.async_create_issue` or custom repair flow registrations (beyond the standard re-auth) were found in the codebase.

## Suggestions

To make the `nest` integration compliant with the `repair-issues` rule, consider the following:

1.  **Handle `ConfigurationException` in `async_setup_entry` with a Repair Issue:**
    *   **Problem:** In `homeassistant/components/nest/__init__.py` (around line 223), `ConfigurationException` during setup leads to a logged error and setup failure.
    *   **Suggestion:** Instead of just logging, create a repair issue.
        *   Use `ir.async_create_issue` with `is_fixable=False` (as the fix is likely in the Google Cloud Console).
        *   The issue description should guide the user to check their SDM API and Pub/Sub configurations (topic, subscription, API enablement, billing).
        *   Provide a `learn_more_url` pointing to the Nest integration's troubleshooting documentation.
    *   **Example Code Snippet (conceptual, to be placed in `__init__.py`):**
        ```python
        from homeassistant.helpers import issue_registry as ir
        # ... other imports ...
        from .const import DOMAIN, CONF_SUBSCRIPTION_NAME, CONF_TOPIC_NAME # Add relevant consts

        # ... inside async_setup_entry ...
        except ConfigurationException as err:
            _LOGGER.error("Configuration error: %s", err)
            # Get topic/subscription names if available in entry data for more specific messaging
            topic_name = entry.data.get(CONF_TOPIC_NAME, "unknown")
            subscription_name = entry.data.get(CONF_SUBSCRIPTION_NAME, "unknown")
            ir.async_create_issue(
                hass,
                DOMAIN,
                "sdm_configuration_error",  # Unique identifier for this type of issue
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="sdm_configuration_error",
                translation_placeholders={
                    "error_message": str(err),
                    "topic_name": topic_name,
                    "subscription_name": subscription_name,
                    "docs_url": "https://www.home-assistant.io/integrations/nest/#troubleshooting" # Update with specific troubleshooting link
                },
                learn_more_url="https://www.home-assistant.io/integrations/nest/#troubleshooting" # Update link
            )
            # Consider raising ConfigEntryNotReady instead of returning False to align with other setup failures
            raise ConfigEntryNotReady(f"Configuration error: {err}") from err
        ```
    *   **Corresponding `strings.json` entry (under `issues`):**
        ```json
        "sdm_configuration_error": {
          "title": "Nest Configuration Error",
          "description": "The Nest integration encountered a configuration error: {error_message}.\nThis often indicates a problem with your Smart Device Management (SDM) API or Pub/Sub setup in your Google Cloud Project for topic '{topic_name}' and subscription '{subscription_name}'.\n\nPlease verify:\n1. The SDM API is enabled.\n2. The Pub/Sub API is enabled.\n3. Your Pub/Sub topic and subscription are correctly configured and linked to your Device Access Project.\n4. Billing is active for your Google Cloud Project.\n\nRefer to the [Nest integration documentation]({docs_url}) for detailed troubleshooting steps."
        }
        ```

2.  **Create a Repair Issue for "Relation Update" (Device Structure Changes):**
    *   **Problem:** In `homeassistant/components/nest/__init__.py` (around line 135), a `relation_update` event only logs a message.
    *   **Suggestion:** Create a repair issue to inform the user and allow them to reload the integration.
        *   Use `ir.async_create_issue` with `is_fixable=True`.
        *   The `issue_domain` should be `DOMAIN` (`nest`).
        *   The `issue_id` could be something like `relation_update_reload_needed`.
        *   Pass `data={"entry_id": self._config_entry.entry_id}` to `ir.async_create_issue`.
        *   Implement a simple repair flow (e.g., in a new `homeassistant/components/nest/repairs.py`) that handles this `issue_id` and reloads the specified config entry.
    *   **Example Code Snippet (conceptual, in `__init__.py` `SignalUpdateCallback.async_handle_event`):**
        ```python
        from homeassistant.helpers import issue_registry as ir
        # ...
        if event_message.relation_update:
            _LOGGER.info("Devices or homes have changed; Need reload to take effect for entry %s", self._config_entry.entry_id)
            # Create a unique issue ID per entry to prevent conflicts if multiple entries exist
            # and to allow re-raising if closed and it happens again.
            # Or, ensure the repair flow handles idempotency if the issue is already open.
            issue_id = f"relation_update_{self._config_entry.entry_id}"
            # Check if this specific issue is already open for this entry_id
            # For simplicity, here we assume we create it. Real implementation should check existing issues.
            if not ir.async_issue_exists(self._hass, DOMAIN, issue_id):
                ir.async_create_issue(
                    self._hass,
                    DOMAIN,
                    issue_id, # This specific instance of the issue
                    is_fixable=True,
                    issue_domain=DOMAIN, # Links to a repair flow in 'nest'
                    data={"entry_id": self._config_entry.entry_id, "entry_title": self._config_entry.title},
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="relation_update_reload_needed",
                    # translation_placeholders can be inferred from 'data' by the frontend if structured well in strings.json
                )
            return
        ```
    *   **Corresponding `strings.json` entry (under `issues`):**
        ```json
        "relation_update_reload_needed": {
          "title": "Nest Device Structure Changed",
          "description": "The structure of your Nest devices or homes (for entry '{entry_title}') has changed according to Google. To apply these changes in Home Assistant, the Nest integration needs to be reloaded.\n\nClick 'Fix Now' to reload the integration.",
          "fix_flow": {
            "confirm": {
              "title": "Reload Nest Integration",
              "description": "This will reload the Nest integration for '{entry_title}'. Proceed?",
              "submit": "Reload"
            }
          }
        }
        ```
    *   **Repair Flow (in `homeassistant/components/nest/repairs.py`):**
        ```python
        from homeassistant.components.repairs import ConfirmRepairFlow
        from homeassistant.core import HomeAssistant

        class NestReloadIntegrationFlow(ConfirmRepairFlow):
            """Repair flow to reload a Nest config entry."""

            async def async_step_init(self, user_input=None):
                """Handle the first step of the repair flow."""
                # For simple flows, init can directly go to confirm
                return await super().async_step_init(user_input)

            async def async_step_confirm(self, user_input=None):
                """Handle the confirm step of the repair flow."""
                if user_input is not None:
                    entry_id = self.issue_data.get("entry_id")
                    if entry_id:
                        await self.hass.config_entries.async_reload(entry_id)
                        return self.async_create_entry(data={})
                    # Handle error: entry_id not found
                    return self.async_abort(reason="missing_entry_id") # Add to strings.json

                # issue_data comes from ir.async_create_issue's data parameter
                entry_title = self.issue_data.get("entry_title", "this Nest configuration")
                return self.async_show_form(
                    step_id="confirm",
                    description_placeholders={"entry_title": entry_title},
                )

        async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data: dict | None) -> NestReloadIntegrationFlow | None:
            """Create a Nest repair flow."""
            # issue_id here is the one passed to ir.async_create_issue, e.g., "relation_update_ENTRYID"
            # For this example, we assume the flow is for any issue starting with "relation_update_"
            if issue_id.startswith("relation_update_"):
                return NestReloadIntegrationFlow(issue_id, data)
            return None # Or raise an error for unknown fix flows

        async def async_setup(hass: HomeAssistant, config: dict) -> bool:
            """Register the Nest repair flow handler."""
            hass.helpers.repair.async_register_flow_handler(
                "nest", # Domain
                "nest_repair_flow_handler", # A name for this handler
                async_create_fix_flow
            )
            return True
        ```
        *Note: The repair flow registration would typically happen in `__init__.py` or a setup function called from there. If `repairs.py` has an `async_setup`, it needs to be called.*
        A simpler approach for the repair flow is to use `ConfirmRepairFlow` if it's just a confirmation and reload. The `translation_key` for the issue itself can point to a `fix_flow` section in `strings.json` as shown above, and HA can often handle simple confirm-style flows based on that. For `NestReloadIntegrationFlow`, the `strings.json` for its `confirm` step would be derived from the `issues.relation_update_reload_needed.fix_flow.confirm` structure.

3.  **Handle Pub/Sub Issues Post-Setup:**
    *   **Problem:** If a Pub/Sub subscription becomes invalid after initial setup (e.g., deleted by user, permissions changed), `SubscriberException` or `ApiException` might occur.
    *   **Suggestion:** Detect specific, user-fixable Pub/Sub errors from these exceptions.
        *   Create a repair issue using `ir.async_create_issue` with `is_fixable=False`.
        *   Guide the user to check their Google Cloud Pub/Sub console, referencing the specific subscription name (from `entry.data`).
    *   **Example Code Snippet (conceptual, in `__init__.py`):**
        ```python
        # ... inside async_setup_entry or relevant error handling ...
        except SubscriberException as err:
            subscription_name = entry.data.get(CONF_SUBSCRIPTION_NAME)
            if "subscription not found" in str(err).lower() and subscription_name: # Example check
                ir.async_create_issue(
                    hass,
                    DOMAIN,
                    f"pubsub_subscription_deleted_{entry.entry_id}",
                    is_fixable=False,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="pubsub_subscription_deleted",
                    translation_placeholders={
                        "subscription_name": subscription_name,
                        "learn_more_url": "https_url_to_nest_docs_pubsub"
                    },
                    learn_more_url="https_url_to_nest_docs_pubsub"
                )
            # Handle other subscriber exceptions or re-raise
            raise ConfigEntryNotReady(f"Subscriber error: {err!s}") from err
        ```
    *   **Corresponding `strings.json` entry (under `issues`):**
        ```json
        "pubsub_subscription_deleted": {
          "title": "Nest Pub/Sub Subscription Missing",
          "description": "The Pub/Sub subscription '{subscription_name}' used by the Nest integration appears to be missing or inaccessible in your Google Cloud Project. This will prevent real-time updates from your Nest devices.\n\nPlease recreate or verify the subscription in the Google Cloud Console and ensure it's correctly linked to your Pub/Sub topic.\n\nRefer to the [Nest integration documentation]({learn_more_url}) for guidance on setting up Pub/Sub."
        }
        ```

By implementing these suggestions, the `nest` integration will provide a more user-friendly experience for troubleshooting common operational issues, aligning better with the `repair-issues` quality scale rule. Remember to add all new translation keys to `strings.json`.

_Created at 2025-05-28 23:16:12. Prompt tokens: 32319, Output tokens: 3583, Total tokens: 41446_
