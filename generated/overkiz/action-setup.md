# overkiz: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **exempt**                                                               |
| Reason | The integration does not register any custom services.                   |

## Overview

The `action-setup` rule does not apply to the `overkiz` integration.

This rule specifies that custom service actions provided by an integration should be registered within the `async_setup` function, rather than `async_setup_entry`. This practice ensures that services are discoverable and can be validated by Home Assistant even if the corresponding configuration entry for the integration is not currently loaded.

A thorough review of the `overkiz` integration's codebase, including its main `__init__.py` file and all platform-specific setup files (e.g., `light.py`, `cover.py`, `climate/__init__.py`, etc.), reveals no instances where the integration registers custom services using `hass.services.async_register`.

The `overkiz` integration primarily focuses on setting up entities (lights, covers, sensors, etc.) based on devices discovered via the Overkiz API. These entities will respond to standard Home Assistant services associated with their respective platforms (e.g., `light.turn_on`, `cover.set_cover_position`). However, the integration does not define or register any new, unique service actions specific to the `overkiz` domain that would fall under the scope of the `action-setup` rule.

Since the `overkiz` integration does not register custom services, the requirements regarding where and how these services should be set up (as dictated by the `action-setup` rule) are not applicable.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:07:16. Prompt tokens: 87117, Output tokens: 440, Total tokens: 89734_
