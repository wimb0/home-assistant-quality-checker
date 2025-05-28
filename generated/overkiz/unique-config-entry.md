# overkiz: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `unique-config-entry` rule requires that an integration prevents the same device or service from being set up multiple times. This is typically achieved by assigning a `unique_id` to the configuration entry during the config flow and aborting if an entry with that `unique_id` already exists.

This rule applies to the `overkiz` integration because it has `config_flow: true` in its `manifest.json`, indicating it uses a configuration flow for setup.

The `overkiz` integration correctly follows this rule. It uses the gateway ID as the `unique_id` for the config entry.

**Evidence from `config_flow.py`:**

1.  **Setting the Unique ID:**
    In the `async_validate_input` method, which is called during both cloud and local API setup, the integration retrieves gateway information and sets the unique ID:
    ```python
    # homeassistant/components/overkiz/config_flow.py
    async def async_validate_input(self, user_input: dict[str, Any]) -> dict[str, Any]:
        # ...
        if gateways := await client.get_gateways():
            for gateway in gateways:
                if is_overkiz_gateway(gateway.id):
                    await self.async_set_unique_id(gateway.id, raise_on_progress=False)
                    break
        return user_input
    ```

2.  **Aborting if Unique ID is Configured (User-initiated flows):**
    In both `async_step_cloud` and `async_step_local` methods, after the input is successfully validated (which includes setting the unique ID via `async_validate_input`), the integration checks if an entry with this unique ID already exists and aborts if it does:
    ```python
    # homeassistant/components/overkiz/config_flow.py
    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # ...
        if user_input:
            # ... (validation logic that calls async_validate_input) ...
            else:
                # ... (reauth logic) ...
                # Create new entry
                self._abort_if_unique_id_configured() # <--- Key check
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
        # ...
    ```
    A similar pattern is present in `async_step_local`:
    ```python
    # homeassistant/components/overkiz/config_flow.py
    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # ...
        if user_input:
            # ... (validation logic that calls async_validate_input) ...
            else:
                # ... (reauth logic) ...
                # Create new entry
                self._abort_if_unique_id_configured() # <--- Key check
                return self.async_create_entry(
                    title=user_input[CONF_HOST], data=user_input
                )
        # ...
    ```

3.  **Aborting if Unique ID is Configured (Discovery flows):**
    For discovery flows (`async_step_dhcp` and `async_step_zeroconf`), the unique ID is set based on the discovered gateway ID, and then `_abort_if_unique_id_configured()` is called directly:
    ```python
    # homeassistant/components/overkiz/config_flow.py
    async def _process_discovery(self, gateway_id: str) -> ConfigFlowResult:
        """Handle discovery of a gateway."""
        await self.async_set_unique_id(gateway_id)
        self._abort_if_unique_id_configured() # <--- Key check
        self.context["title_placeholders"] = {"gateway_id": gateway_id}
        return await self.async_step_user()
    ```
    Both `async_step_dhcp` and `async_step_zeroconf` call `_process_discovery`.

This implementation ensures that each Overkiz gateway can only be configured once, preventing duplicate entries and associated issues.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:16:20. Prompt tokens: 87626, Output tokens: 1122, Total tokens: 90166_
