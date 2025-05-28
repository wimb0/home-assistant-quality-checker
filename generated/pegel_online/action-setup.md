```markdown
# pegel_online: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup) |
| Status | **exempt**                                                               |
| Reason | The integration does not register any custom Home Assistant services.    |

## Overview

The `action-setup` rule requires integrations that add custom service actions to register them in the `async_setup` function rather than `async_setup_entry`. This ensures service validation is possible even when configuration entries are not loaded.

Upon reviewing the code for the `pegel_online` integration (`homeassistant/components/pegel_online/__init__.py`, `sensor.py`, etc.), there are no calls to `hass.services.async_register` in either `async_setup` (which doesn't exist in this integration) or `async_setup_entry`. The integration primarily sets up sensor entities based on configuration entries.

Since the `pegel_online` integration does not define or register any custom service actions, the requirements of the `action-setup` rule do not apply. Therefore, the integration is exempt from this rule.
```

_Created at 2025-05-25 11:21:44. Prompt tokens: 6013, Output tokens: 311, Total tokens: 6801_
