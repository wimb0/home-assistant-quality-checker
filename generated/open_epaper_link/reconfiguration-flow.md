# open_epaper_link: reconfiguration-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [reconfiguration-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow)                                                     |
| Status | **exempt**                                       |
| Reason | The only configuration item in `ConfigEntry.data` (`CONF_HOST`) is also the integration's `unique_id`. Since `unique_id` is immutable after entry creation, this setting cannot be changed via a reconfigure flow. There are no other reconfigurable items in `ConfigEntry.data`. |

## Overview

The `reconfiguration-flow` rule requires integrations to provide a way for users to update their configuration (typically `ConfigEntry.data`) without removing and re-adding the integration. This is useful if settings like an IP address or API key change.

The `open_epaper_link` integration uses `CONF_HOST` (the IP address or hostname of the OpenEPaperLink AP) as its primary configuration item. This is set during the initial `async_step_user` in `config_flow.py`:
```python
# config_flow.py
# ...
            return self.async_create_entry(
                title=info["title"],
                data={CONF_HOST: self._host}
            )
```
The `CONF_HOST` is also used as the `unique_id` for the config entry:
```python
# config_flow.py
# ...
            if not error:
                await self.async_set_unique_id(self._host)
                self._abort_if_unique_id_configured()
# ...
```
Home Assistant `ConfigEntry` objects have an immutable `unique_id` once created. This means that `CONF_HOST`, being the `unique_id`, cannot be changed for an existing config entry.

The rule's exception states: "Integrations that don't have settings in their configuration flow are exempt from this rule." While `open_epaper_link` *does* have `CONF_HOST` as a setting, the Home Assistant developer documentation for [Configuring Reconfiguration](https://developers.home-assistant.io/docs/config_entries_config_flow_handler#reconfigure) further clarifies: "If your integration does not have any data that can be reconfigured, you don't need to implement this."

Since `CONF_HOST` is the only item in `ConfigEntry.data` for `open_epaper_link`, and it cannot be reconfigured due to its role as the immutable `unique_id`, there is no data that can be reconfigured via a `reconfiguration-flow` for `ConfigEntry.data`.

The integration does have an `OptionsFlowHandler` which allows users to change settings stored in `ConfigEntry.options` (like `blacklisted_tags`, debounce intervals). These are handled correctly by the options flow and are distinct from the core configuration data targeted by the `reconfiguration-flow` rule.
The integration also implements `async_step_reauth` and `async_step_reauth_confirm`, which allow re-validating the connection to the *existing* `CONF_HOST` but do not allow changing it.

Therefore, the integration is considered **exempt** from this rule because its only core configuration setting (`CONF_HOST`) is immutable by design as it serves as the `unique_id`. If the AP's host changes, the user must remove and re-add the integration, as it's treated as a new device instance from Home Assistant's perspective given the current unique ID strategy.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 21:06:42. Prompt tokens: 60964, Output tokens: 849, Total tokens: 69416_
