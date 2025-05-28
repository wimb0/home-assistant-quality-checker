# pegel_online: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |

## Overview

This rule requires integrations using config flows to prevent the user from setting up the same device or service instance multiple times. This typically involves checking for existing configuration entries that represent the same unique entity before creating a new one.

The `pegel_online` integration uses a config flow (`config_flow.py`) to allow users to discover and select a specific measuring station to add to Home Assistant. Since each station is a unique service instance, this rule applies.

The integration successfully follows this rule. In the `async_step_select_station` method of the config flow, after the user selects a specific station identified by its UUID (`user_input[CONF_STATION]`), the flow performs the necessary checks:

1.  It sets the unique identifier for the *configuration entry* using the station's UUID:
    ```python
    await self.async_set_unique_id(user_input[CONF_STATION])
    ```
    (See `homeassistant/components/pegel_online/config_flow.py`, line 60)
    The station's UUID is guaranteed to be unique for each station provided by the API.
2.  It immediately checks if a configuration entry with this specific unique ID (the station UUID) already exists for the `pegel_online` domain:
    ```python
    self._abort_if_unique_id_configured()
    ```
    (See `homeassistant/components/pegel_online/config_flow.py`, line 61)

If `_abort_if_unique_id_configured()` finds an existing entry with the same unique ID, the config flow is aborted with the standard "already configured" error message, preventing the duplicate setup of the same station. This implements one of the recommended patterns described in the rule documentation.

## Suggestions

No suggestions needed. The integration correctly implements the unique config entry check.

_Created at 2025-05-25 11:22:54. Prompt tokens: 6522, Output tokens: 522, Total tokens: 7762_
