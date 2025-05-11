# wled: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not register any custom domain-level services. |

## Overview

The `action-setup` rule mandates that custom service actions an integration provides to Home Assistant should be registered within the `async_setup` function. This practice ensures that these service actions are always available for purposes like automation validation, even if the associated configuration entry for the integration is not currently loaded. The service handler itself should then validate if the target config entry is loaded and raise `ServiceValidationError` if not.

This rule does **not apply** to the `wled` integration.

A thorough review of the `wled` integration's codebase, particularly its `__init__.py` file, reveals that it does not register any custom domain-level services using `hass.services.async_register(DOMAIN, ...)`. The `async_setup` function in `__init__.py` is used for setting up a shared `WLEDReleasesDataUpdateCoordinator` but does not involve service registration:

```python
# __init__.py
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WLED integration.

    We set up a single coordinator for fetching WLED releases, which
    is used across all WLED devices (and config entries) to avoid
    fetching the same data multiple times for each.
    """
    hass.data[WLED_KEY] = WLEDReleasesDataUpdateCoordinator(hass)
    await hass.data[WLED_KEY].async_request_refresh()
    return True
```

The `wled` integration functions by providing various entities (lights, switches, sensors, buttons, selects, and update entities). Interactions with these WLED devices are managed through standard Home Assistant services that correspond to these entity platforms (e.g., `light.turn_on` for light entities, `button.press` for button entities, `switch.turn_on` for switch entities). These standard services are registered by Home Assistant's core or the respective entity platforms, not as custom services defined and registered directly by the `wled` integration for its own domain.

Since the `wled` integration does not introduce its own unique service actions (e.g., a hypothetical `wled.apply_custom_scene` service), the requirements of the `action-setup` rule regarding the registration location of such services are not applicable.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:23:57. Prompt tokens: 21814, Output tokens: 623, Total tokens: 24468_
