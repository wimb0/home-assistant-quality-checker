# nmbs: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not register any custom services. |

## Overview

The `action-setup` rule requires that custom service actions provided by an integration are registered in the `async_setup` function of `__init__.py`. This ensures that services are discoverable and can be validated even if the associated configuration entry is not loaded.

A review of the `nmbs` integration's code, particularly `__init__.py` and `sensor.py`, shows that it does not define or register any custom services using `hass.services.async_register()`. The integration primarily provides sensor entities.

Since the `nmbs` integration does not offer any custom services, the `action-setup` rule, which governs how such services should be registered, does not apply.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:17:52. Prompt tokens: 10072, Output tokens: 274, Total tokens: 11149_
