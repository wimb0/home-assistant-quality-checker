# jewish_calendar: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `unique-config-entry` rule requires that an integration must not allow the same device or service to be set up twice. This is to prevent duplicated devices, entities, and potential unique identifier collisions.

This rule applies to the `jewish_calendar` integration because it uses a config flow (`config_flow: true` in `manifest.json`) for setup, making it susceptible to accidental duplicate setups if not handled.

The `jewish_calendar` integration **fully follows** this rule. It achieves this by specifying `"single_config_entry": true` in its `manifest.json` file:

```json
// homeassistant/components/jewish_calendar/manifest.json
{
  // ...
  "single_config_entry": true
  // ...
}
```

The `single_config_entry: true` directive instructs Home Assistant core to allow only one configuration entry for this integration. If a user attempts to add the `jewish_calendar` integration through the UI when an instance is already configured, Home Assistant will automatically abort the new setup process. This is confirmed by the presence of an `already_configured` abort reason in the integration's `strings.json`:

```json
// homeassistant/components/jewish_calendar/strings.json
{
  // ...
  "config": {
    // ...
    "abort": {
      "already_configured": "[%key:common::config_flow::abort::already_configured_device%]"
      // ...
    }
  }
}
```

This mechanism directly prevents the service from being set up more than once, thus satisfying the requirements of the `unique-config-entry` rule. The `config_flow.py` does not need to implement explicit checks like `self.async_set_unique_id()` or `self._async_abort_entries_match()` because the `single_config_entry` manifest setting handles this at the core level.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:11:59. Prompt tokens: 14093, Output tokens: 556, Total tokens: 17200_
