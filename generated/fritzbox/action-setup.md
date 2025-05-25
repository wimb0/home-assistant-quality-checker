```markdown
# fritzbox: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not register any custom Home Assistant services. |

## Overview

The `action-setup` rule requires integrations that register custom Home Assistant services to do so within the integration's `async_setup` function (in `__init__.py`) instead of `async_setup_entry`. This ensures that service validation is possible even if a specific configuration entry is not currently loaded.

Upon reviewing the provided code for the `fritzbox` integration, specifically the `homeassistant/components/fritzbox/__init__.py` file and the various platform files (`binary_sensor.py`, `button.py`, `climate.py`, `cover.py`, `light.py`, `sensor.py`, `switch.py`), there are no instances where the integration registers custom services using `hass.services.async_register`.

The `fritzbox` integration exposes the functionality of connected FRITZ!SmartHome devices through standard Home Assistant entity types (like `switch.turn_on`, `climate.set_temperature`, `button.press`), which rely on the entity methods being called by Home Assistant's core service mechanisms.

Since the `fritzbox` integration does not define or register any custom services, the requirements of the `action-setup` rule do not apply to this integration.

No suggestions needed.
```

_Created at 2025-05-25 11:19:38. Prompt tokens: 19108, Output tokens: 391, Total tokens: 20201_
