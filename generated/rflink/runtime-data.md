# rflink: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [rflink](https://www.home-assistant.io/integrations/rflink/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **exempt**                                       |
| Reason | The integration is configured via YAML and does not use `ConfigEntry`, so `ConfigEntry.runtime_data` is not applicable. |

## Overview

The `runtime-data` rule requires integrations to use the `ConfigEntry.runtime_data` attribute for storing data needed during the lifetime of a configuration entry, especially for data not persisted to configuration file storage.

This rule does not apply to the `rflink` integration. The `rflink` integration is a legacy integration that is set up and configured via `configuration.yaml`. This can be identified by the presence of `async_setup(hass: HomeAssistant, config: ConfigType)` and `CONFIG_SCHEMA` in its `__init__.py` file. The `runtime-data` rule is specifically relevant for integrations that utilize the `ConfigEntry` system, which typically involves an `async_setup_entry(hass: HomeAssistant, entry: ConfigEntry)` function for setting up the integration from a config entry.

The `rflink` integration's `__init__.py` does not import or use `ConfigEntry` from `homeassistant.config_entries`, nor does it implement `async_setup_entry`. Therefore, the concept of `ConfigEntry.runtime_data` is not applicable to its current architecture. The manifest file also indicates `"quality_scale": "legacy"`, which often aligns with integrations not using the modern config entry system.

## Suggestions
No suggestions needed.

_Created at 2025-05-28 13:31:54. Prompt tokens: 17700, Output tokens: 409, Total tokens: 19107_
