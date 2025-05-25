```markdown
# pegel_online: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The rule `integration-owner` requires that an integration specifies one or more GitHub users as codeowners in its `manifest.json` file. This indicates who is responsible for maintaining the integration.

This rule applies to the `pegel_online` integration. The provided `manifest.json` file for `pegel_online` includes the required `codeowners` field and specifies a GitHub username:

```json
{
  "domain": "pegel_online",
  "name": "PEGELONLINE",
  "codeowners": ["@mib1185"], // <- This line satisfies the rule
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/pegel_online",
  "integration_type": "service",
  "iot_class": "cloud_polling",
  "loggers": ["aiopegelonline"],
  "requirements": ["aiopegelonline==0.1.1"]
}
```

Because the `codeowners` field is present and contains at least one valid entry (`"@mib1185"`), the integration follows the `integration-owner` rule.

## Suggestions

No suggestions needed.

```

_Created at 2025-05-25 11:23:35. Prompt tokens: 5776, Output tokens: 388, Total tokens: 6447_
