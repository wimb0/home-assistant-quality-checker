```markdown
# pegel_online: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions) |
| Status | **exempt**                                                               |
| Reason | The integration does not define or expose any custom Home Assistant services. |

## Overview

The `action-exceptions` rule requires that integrations defining custom Home Assistant services raise appropriate exceptions (`ServiceValidationError` or `HomeAssistantError`) when these service actions encounter failures.

Based on the provided code, the `pegel_online` integration does not define or register any custom services that users can call (e.g., via the Developer Tools > Services page or automations).

Looking through the files (`__init__.py`, `config_flow.py`, `coordinator.py`, `sensor.py`, etc.), there are no instances of `hass.services.async_register` or a `services.yaml` file defining service schemas. The integration primarily focuses on fetching data from an external API and exposing it as sensors. While it handles API communication errors appropriately within the config flow (`config_flow.py`) and the data update coordinator (`coordinator.py`), these are not considered "service actions" in the context of this specific rule.

Therefore, since there are no custom service actions defined, the `action-exceptions` rule does not apply to this integration.
```

_Created at 2025-05-25 11:23:15. Prompt tokens: 5889, Output tokens: 354, Total tokens: 7165_
