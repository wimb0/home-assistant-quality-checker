```markdown
# samsungtv: diagnostics

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [diagnostics](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics)                                                     |
| Status | **done**                                                                 |

## Overview

The `diagnostics` rule requires integrations to provide diagnostic information to aid in debugging, ensuring no sensitive data is exposed. This rule applies to all integrations.

The `samsungtv` integration fully complies with this rule. It includes a `diagnostics.py` file which implements the required `async_get_config_entry_diagnostics` function.

The `async_get_config_entry_diagnostics` function in `homeassistant/components/samsungtv/diagnostics.py` retrieves two main pieces of information:

1.  The configuration entry data (`entry.as_dict()`).
2.  The device information obtained from the bridge (`coordinator.bridge.async_device_info()`).

Crucially, the integration uses `async_redact_data` on the config entry data, explicitly redacting `CONF_TOKEN` and `CONF_SESSION_ID` as defined in the `TO_REDACT` set within `diagnostics.py`. This prevents sensitive authentication details from being included in the diagnostics output.

The device information (`async_device_info`) typically includes details like model name, manufacturer, UDN, MAC address, etc., which are generally not considered sensitive data in the context of this rule (which focuses on passwords, tokens, and coordinates).

By providing relevant configuration and device details while redacting sensitive credentials, the integration effectively implements diagnostics according to the rule's requirements.
```

_Created at 2025-05-25 11:31:01. Prompt tokens: 29953, Output tokens: 408, Total tokens: 31062_
