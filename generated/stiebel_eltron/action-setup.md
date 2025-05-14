# stiebel_eltron: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **exempt**                                                               |
| Reason | This integration does not register any custom, domain-specific services. |

## Overview

The rule `action-setup` mandates that any custom service actions an integration provides should be registered within the `async_setup` function, rather than `async_setup_entry`. This ensures service availability for validation purposes even if a specific configuration entry is not loaded. The service handler itself should then validate if the required config entry is loaded and raise `ServiceValidationError` if necessary.

This rule is **not applicable** to the `stiebel_eltron` integration.

A thorough review of the `stiebel_eltron` codebase, particularly `homeassistant/components/stiebel_eltron/__init__.py`, reveals that the integration does not register any custom, domain-specific services using `hass.services.async_register(DOMAIN, ...)`.

The `stiebel_eltron` integration primarily provides entities through the `climate` platform, as indicated in its `manifest.json` (`"platforms": ["climate"]`) and implemented in `homeassistant/components/stiebel_eltron/climate.py`. The services associated with these entities, such as `climate.set_temperature` or `climate.set_hvac_mode` (handled by methods like `set_temperature` and `set_hvac_mode` in the `StiebelEltron` class in `climate.py`), are standard services provided and managed by the climate entity platform itself. These are not custom services defined by the `stiebel_eltron` integration in the context of the `action-setup` rule.

The `action-setup` rule targets services that an integration adds beyond standard entity services, like the example `SERVICE_GET_SCHEDULE` provided in the rule description. Since `stiebel_eltron` does not define or register such custom services, the requirements and rationale behind the `action-setup` rule do not apply to it.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 14:52:41. Prompt tokens: 6229, Output tokens: 525, Total tokens: 8730_
