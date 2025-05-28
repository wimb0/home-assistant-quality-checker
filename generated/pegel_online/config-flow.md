```markdown
# pegel_online: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule requires integrations that need configuration to be set up via the Home Assistant user interface using a config flow, storing the persistent configuration data in `ConfigEntry.data`. This integration, `pegel_online`, requires configuration (specifically, selecting a measuring station), making this rule applicable.

Based on the provided code, the integration fully follows this rule:

1.  **`manifest.json`**: The presence of `"config_flow": true` in `homeassistant/components/pegel_online/manifest.json` indicates that the integration is designed to be set up via a config flow.
2.  **`config_flow.py`**: The file `homeassistant/components/pegel_online/config_flow.py` contains a `FlowHandler` class that inherits from `ConfigFlow`.
    *   It implements the required `async_step_user` method to initiate the configuration process.
    *   It utilizes appropriate selectors (`LocationSelector`, `NumberSelector`) for user input (location and radius to find nearby stations).
    *   It includes logic to fetch stations based on user input and handles potential connection errors and cases where no stations are found.
    *   It transitions to a `async_step_select_station` where it presents the found stations using a `SelectSelector`.
    *   Upon selecting a station, it calls `self.async_set_unique_id` using the station's UUID, ensuring uniqueness, and uses `self._abort_if_unique_id_configured()` to prevent duplicate entries.
    *   Finally, it creates the configuration entry using `self.async_create_entry`, passing the selected station UUID (and other data) in the `data` dictionary, correctly storing the configuration in `ConfigEntry.data`.
3.  **`__init__.py`**: The `async_setup_entry` function in `homeassistant/components/pegel_online/__init__.py` retrieves the configured station UUID using `entry.data[CONF_STATION]`, confirming that the configuration is stored and accessed via the config entry's data.
4.  **`strings.json`**: The `homeassistant/components/pegel_online/strings.json` file provides translations for the config flow steps, data fields, and error messages (`cannot_connect`, `no_stations`), contributing to a user-friendly experience.

The integration successfully implements a multi-step config flow that guides the user through selecting a station based on location, stores the selected station ID in the config entry's data, and uses this data for setup, adhering to the requirements of the `config-flow` rule.

## Suggestions

No suggestions needed. The integration correctly implements a config flow and stores configuration in the `ConfigEntry.data`.
```

_Created at 2025-05-25 11:22:06. Prompt tokens: 6189, Output tokens: 720, Total tokens: 8272_
