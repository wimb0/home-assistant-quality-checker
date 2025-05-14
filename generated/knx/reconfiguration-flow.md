# knx: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [knx](https://www.home-assistant.io/integrations/knx/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **todo**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `reconfiguration-flow` rule requires that integrations provide a way for users to reconfigure settings without needing to remove and re-add the integration, typically by implementing an `async_step_reconfigure` method in the `config_flow.py`.

The `knx` integration has `config_flow: true` in its `manifest.json` and its configuration flow (`homeassistant/components/knx/config_flow.py`) allows for setting various parameters like connection type, IP addresses, ports, and security settings. Therefore, the rule applies to this integration and it is not exempt under the "no settings in config flow" clause.

Currently, the `knx` integration does **not** fully follow this rule. While it has a comprehensive `OptionsFlow` (`KNXOptionsFlow` in `config_flow.py`) that allows users to change most, if not all, relevant settings after initial setup, it does not explicitly implement the `async_step_reconfigure` method in its main `ConfigFlow` class (`KNXConfigFlow`).

Home Assistant core provides a fallback mechanism where, if `async_step_reconfigure` is missing, it will use the `OptionsFlow` instead when a reconfiguration is triggered (e.g., if an entry is in an error state). This means users can functionally reconfigure the KNX integration.

However, the rule's example implementation explicitly shows an `async_step_reconfigure` method. Furthermore, the `knx` integration's own `quality_scale.yaml` file marks `reconfiguration-flow` as `todo`. This indicates a consensus that an explicit implementation is desired or required for full compliance, rather than relying solely on the `OptionsFlow` fallback. An explicit reconfigure flow can also offer a more tailored experience or specific checks when an integration *needs* reconfiguration due to an error, as opposed to a user proactively changing options.

Specifically, the file `homeassistant/components/knx/config_flow.py` defines `KNXConfigFlow` but does not include an `async_step_reconfigure` method.

## Suggestions

To make the `knx` integration compliant with the `reconfiguration-flow` rule, an `async_step_reconfigure` method should be added to the `KNXConfigFlow` class in `homeassistant/components/knx/config_flow.py`.

This method should:
1.  Be initiated when Home Assistant determines the config entry needs reconfiguration. The `self.reconfigure_entry` attribute will be populated with the `ConfigEntry` to be reconfigured.
2.  Allow the user to modify the core connection parameters (e.g., connection type, host, port, individual address, security settings) and potentially other settings that might cause the integration to fail (like rate limits if misconfigured, though less common).
3.  Leverage the existing common flow logic in `KNXCommonFlow` for presenting forms and collecting user input for these settings. The `self.initial_data` for `KNXCommonFlow` should be populated from `self.reconfigure_entry.data`.
4.  Upon successful validation and collection of new settings, update the existing config entry using `self.async_update_reload_and_abort(self.reconfigure_entry, data=updated_config_data)`.

**Example Sketch:**

A possible way to integrate this into `KNXConfigFlow` in `homeassistant/components/knx/config_flow.py`, considering the existing `KNXCommonFlow` and its abstract `finish_flow` method:

```python
# In homeassistant/components/knx/config_flow.py

# ... imports ...

class KNXConfigFlow(KNXCommonFlow, ConfigFlow, domain=DOMAIN):
    VERSION = 1
    _is_reconfiguring: bool = False # Flag to indicate reconfigure context

    def __init__(self) -> None:
        """Initialize KNX config flow."""
        super().__init__(initial_data=DEFAULT_ENTRY_DATA)
        self._is_reconfiguring = False

    # ... existing KNXConfigFlow methods (async_get_options_flow, async_step_user) ...

    async def async_step_reconfigure(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        self._is_reconfiguring = True
        # self.reconfigure_entry is set by Home Assistant core
        self.initial_data = self.reconfigure_entry.data
        # Start the common flow, e.g., by directing to the connection_type step or a menu
        return await self.async_step_connection_type(user_input)

    @callback
    def finish_flow(self) -> ConfigFlowResult:
        """Create or update the ConfigEntry."""
        # Consolidate data: defaults, then initial entry data (if reconfiguring) or new entry defaults, then new user input
        current_entry_data = self.reconfigure_entry.data if self._is_reconfiguring and self.reconfigure_entry else {}
        updated_data = DEFAULT_ENTRY_DATA | current_entry_data | self.new_entry_data

        if self._is_reconfiguring:
            if not self.reconfigure_entry:
                # Should not happen if _is_reconfiguring is true
                return self.async_abort(reason="unknown_error")
            
            # Ensure the title is preserved or updated meaningfully
            title = self.new_title or self.reconfigure_entry.title
            
            # Update the entry and signal HA to reload it.
            # The `async_update_reload_and_abort` function is designed for this.
            # However, `finish_flow` is called by common steps.
            # The common step itself should return `async_update_reload_and_abort`.
            # This example assumes finish_flow is the final point from a common step.
            # A more robust implementation might involve the common steps returning data
            # to async_step_reconfigure, which then calls async_update_reload_and_abort.

            # For simplicity here, we show direct update and abort.
            # In a real implementation, the step calling this finish_flow would need to
            # return the ConfigFlowResult from async_update_reload_and_abort.
            # This means KNXCommonFlow's steps need to be aware of the context
            # or return data to the main flow (ConfigFlow/OptionsFlow).

            # Let's assume the last step of the common flow (e.g., manual_tunnel or routing)
            # will determine how to finalize. If that's the case, this finish_flow
            # should not be called directly in reconfigure mode from the common step.
            # Instead, the common step would return data, and async_step_reconfigure's chain
            # would end with:
            # return self.async_update_reload_and_abort(self.reconfigure_entry, data=updated_data, title=title)
            # This is a placeholder for that logic.
            # For the purpose of this suggestion, the key is to *have* async_step_reconfigure
            # and a path to update the entry.
            self.hass.config_entries.async_update_entry(
                self.reconfigure_entry, data=updated_data, title=title
            )
            # The actual reload is usually triggered by async_update_entry or explicitly.
            # `async_update_reload_and_abort` is preferred.
            return self.async_abort(reason="reconfigure_successful") # This needs to be `async_update_reload_and_abort` if it's the final step.


        # Regular config flow (new entry)
        title = self.new_title or f"KNX {updated_data.get(CONF_KNX_CONNECTION_TYPE, 'Integration')}"
        return self.async_create_entry(
            title=title,
            data=updated_data,
        )

# KNXOptionsFlow would remain largely as is, as it handles options for an already working entry.
# Its finish_flow updates the entry and returns self.async_create_entry(title="", data={})
# which is standard for options flows.

# Note: The above `finish_flow` adaptation is a conceptual sketch.
# A full implementation would need careful handling of how common flow steps
# (in KNXCommonFlow) transition to finalization, ensuring that `async_update_reload_and_abort`
# is correctly used for reconfigurations.
```

By implementing `async_step_reconfigure`, the KNX integration would explicitly support the reconfiguration pathway, aligning with best practices and the rule's intent, even if the underlying UI and logic are shared with the options flow. This provides a clear signal to Home Assistant that the integration can be reconfigured when it's in an error state.

_Created at 2025-05-14 13:39:31. Prompt tokens: 101477, Output tokens: 2111, Total tokens: 110357_
