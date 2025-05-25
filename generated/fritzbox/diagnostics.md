```markdown
# fritzbox: diagnostics

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [diagnostics](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics)                                                     |
| Status | **done**                                                                 |

## Overview

The `diagnostics` rule requires integrations to provide a diagnostics handler to assist users and developers in debugging. This handler should expose relevant information about the integration's state and configuration while redacting sensitive data.

This rule applies to the `fritzbox` integration as it is a hub integration with a config entry.

The integration fully follows this rule. The `fritzbox` integration implements a `diagnostics.py` file containing the required `async_get_config_entry_diagnostics` function. This function retrieves data from the config entry and the data update coordinator (`entry.runtime_data`). It correctly redacts sensitive information (`CONF_USERNAME`, `CONF_PASSWORD`) from the config entry data using `async_redact_data`, as specified by the rule. It also includes the state and attributes of the discovered devices and templates, filtering out internal attributes (starting with `_`), which is a common and good practice for diagnostics output.

Specifically, the file `homeassistant/components/fritzbox/diagnostics.py` defines:
- `TO_REDACT`: A set containing `CONF_USERNAME` and `CONF_PASSWORD`.
- `async_get_config_entry_diagnostics`: This asynchronous function takes `hass` and the `entry` (which is `FritzboxConfigEntry`) as arguments.
- Inside the function, it accesses the `FritzboxDataUpdateCoordinator` via `entry.runtime_data`.
- It redacts the config entry data using `async_redact_data(entry.as_dict(), TO_REDACT)`.
- It retrieves device and template data from the coordinator's `data` attribute (`coordinator.data.devices`, `coordinator.data.templates`).
- It constructs a dictionary for the `data` section of the diagnostics output, including device/template attributes while excluding those starting with `_`, ensuring that implementation details or potentially sensitive internal states are not exposed by default.

This implementation aligns well with the example provided in the rule description and fulfills the requirement for providing useful, yet safe, diagnostic information.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:35:29. Prompt tokens: 18810, Output tokens: 558, Total tokens: 19943_
