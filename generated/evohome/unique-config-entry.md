# evohome: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |

## Overview

The `unique-config-entry` rule requires that an integration must not allow the same device or service to be set up twice. This is typically achieved by assigning a `unique_id` to the configuration entry within the config flow and aborting if an entry with that `unique_id` already exists.

This rule applies to the `evohome` integration because its `manifest.json` declares `"config_flow": true`, indicating it uses a configuration flow for setup.

The `evohome` integration **fully follows** this rule. It ensures uniqueness in the following ways:

1.  **Config Flow Implementation:**
    The integration's config flow, located in `homeassistant/components/evohome/config_flow.py`, uses the Evohome account username as the basis for a unique identifier.
    *   In the `async_step_user` method, when a user provides their credentials:
        ```python
        # homeassistant/components/evohome/config_flow.py
        async def async_step_user(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            # ...
            if user_input is not None:
                self._username = user_input[CONF_USERNAME]
                # ...
                await self.async_set_unique_id(self._username.lower()) # Sets unique_id based on username
                # ...
                try:
                    self._abort_if_unique_id_configured(error="already_configured_account") # Aborts if this unique_id already exists
                    # ...
        ```
        This code snippet demonstrates that the integration sets a `unique_id` based on the lowercase version of the provided username and then calls `self._abort_if_unique_id_configured()`. If a config entry with this username (unique ID) already exists, the flow is aborted, preventing a duplicate setup of the same Evohome account.

    *   Similarly, in the `async_step_import` method, which handles setup from `configuration.yaml`:
        ```python
        # homeassistant/components/evohome/config_flow.py
        async def async_step_import(self, config: EvoConfigFileDictT) -> ConfigFlowResult:
            # ...
            await self.async_set_unique_id(config[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()  # dont import a config if already exists
            # ...
        ```
        This ensures that importing a configuration also respects the uniqueness based on the username.

2.  **Single Config Entry Flag:**
    The `manifest.json` for `evohome` also includes `"single_config_entry": true`.
    ```json
    // homeassistant/components/evohome/manifest.json
    {
      // ...
      "config_flow": true,
      // ...
      "single_config_entry": true
    }
    ```
    This flag instructs Home Assistant that only one configuration entry for the `evohome` domain is allowed. If a user attempts to add the integration via the UI when an entry already exists, Home Assistant Core will prevent the new flow from starting and direct the user to the existing entry. While this is a higher-level constraint, the integration's internal config flow logic (as described in point 1) correctly implements the specific mechanism required by the `unique-config-entry` rule.

The combination of these mechanisms effectively prevents the same Evohome account (service) from being configured multiple times. The config flow's use of `async_set_unique_id` with the username and `_abort_if_unique_id_configured` directly aligns with the example implementation provided in the rule description.

## Suggestions

No suggestions needed.

---

_Created at 2025-05-29 11:50:42. Prompt tokens: 22456, Output tokens: 956, Total tokens: 27190._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
