```markdown
# pegel_online: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **exempt**                                                               |
| Reason | The integration does not store any configurable settings in the config entry that would require a reconfiguration flow. |

## Overview

The rule `reconfiguration-flow` requires integrations with configurable settings in their config flow to implement an `async_step_reconfigure` method. This allows users to update connection details or other settings without removing and re-adding the integration.

The provided code for the `pegel_online` integration includes a configuration flow (`config_flow.py`). However, examining the `async_step_user` and `async_step_select_station` methods, we see that the user provides a location and radius to search for nearby stations, and then selects a specific station based on its unique UUID.

Looking at the `async_create_entry` method in `async_step_select_station`:
```python
        return self.async_create_entry(
            title=self._stations[user_input[CONF_STATION]],
            data=user_input, # user_input here is only {'station': 'uuid'}
        )
```
This shows that the `data` stored in the config entry only contains the selected `CONF_STATION` (the station's UUID). The initial location and radius used to *find* the station are not persisted in the config entry data.

The `async_setup_entry` function in `__init__.py` confirms that only the station UUID is retrieved from the config entry data:
```python
    station_uuid = entry.data[CONF_STATION]
```
The integration instance is tied to this specific station UUID. There are no other settings like hostnames, API keys, usernames, or passwords stored in the config entry that might change over time and require a reconfigure flow to update. If the station's UUID were to change (highly unlikely for a unique identifier) or if the user wanted to monitor a *different* station, adding a new integration instance would be the appropriate action, not reconfiguring the existing one.

Therefore, based on the exception provided in the rule description ("Integrations that don't have settings in their configuration flow are exempt from this rule."), the `pegel_online` integration is exempt as it does not store configurable settings in the config entry data that would necessitate a reconfigure flow.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:25:34. Prompt tokens: 6371, Output tokens: 612, Total tokens: 7675_
