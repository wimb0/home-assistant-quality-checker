# adax: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not register any custom services. |

## Overview

The `action-setup` rule mandates that if an integration provides custom service actions, these actions should be registered within the `async_setup` function. This approach ensures that service calls can be validated and provide informative errors even if the relevant configuration entry is not loaded, which is not always possible if services are registered in `async_setup_entry`.

This rule is applicable to integrations that define and register their own specific services (e.g., `my_integration.custom_action`).

Upon reviewing the codebase for the `adax` integration, specifically the `__init__.py` file and other component files (`climate.py`, `coordinator.py`), there is no indication that the integration registers any custom services. The `__init__.py` file does not contain an `async_setup` function, and there are no calls to `hass.services.async_register` or `hass.services.register` anywhere in the integration's Python files.

The `adax` integration primarily provides `climate` entities by forwarding setup to the `CLIMATE` platform:
```python
# homeassistant/components/adax/__init__.py
PLATFORMS = [Platform.CLIMATE]

async def async_setup_entry(hass: HomeAssistant, entry: AdaxConfigEntry) -> bool:
    # ...
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
```
The services associated with these entities (e.g., `climate.set_temperature`, `climate.set_hvac_mode`) are standard services provided by the climate platform, not custom services defined and registered by the `adax` integration itself.

Since the `adax` integration does not register any custom service actions, the `action-setup` rule, which governs the method of registering such custom services, does not apply.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:02:09. Prompt tokens: 6777, Output tokens: 527, Total tokens: 8679_
