# local_todo: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `integration-owner` rule requires that an integration specifies at least one code owner in its `manifest.json` file. This rule applies to all integrations, as there are no exceptions.

The `local_todo` integration **fully follows** this rule.

The `manifest.json` file for the `local_todo` integration includes a `codeowners` field with a valid GitHub username:

```json
{
  "domain": "local_todo",
  "name": "Local To-do",
  "codeowners": ["@allenporter"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/local_todo",
  "iot_class": "local_polling",
  "requirements": ["ical==9.2.5"]
}
```

Specifically, the line `"codeowners": ["@allenporter"]` designates `@allenporter` as the code owner for this integration, fulfilling the requirements of the rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:38:02. Prompt tokens: 4949, Output tokens: 343, Total tokens: 6452_
