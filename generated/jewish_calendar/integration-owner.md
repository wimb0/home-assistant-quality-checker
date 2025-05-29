# jewish_calendar: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `integration-owner` rule requires that an integration has at least one designated owner specified in its `manifest.json` file. This helps ensure that integrations are maintained and that there is a point of contact for issues and pull requests.

The rule applies to the `jewish_calendar` integration.

The `jewish_calendar` integration **fully follows** this rule. The `manifest.json` file includes a `codeowners` field with a valid GitHub username.

Specifically, the `homeassistant/components/jewish_calendar/manifest.json` file contains:
```json
{
  "domain": "jewish_calendar",
  "name": "Jewish Calendar",
  "codeowners": ["@tsvi"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/jewish_calendar",
  "iot_class": "calculated",
  "loggers": ["hdate"],
  "requirements": ["hdate[astral]==1.1.0"],
  "single_config_entry": true
}
```
The line `"codeowners": ["@tsvi"]` clearly defines `@tsvi` as the code owner for this integration, satisfying the rule's requirements.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:17:22. Prompt tokens: 13347, Output tokens: 404, Total tokens: 14400_
