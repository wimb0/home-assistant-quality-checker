# nest: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `integration-owner` rule requires that an integration specifies one or more code owners in its `manifest.json` file. This ensures that there are designated individuals responsible for the maintenance and stewardship of the integration. The rule applies to all integrations, with no exceptions.

The `nest` integration **fully follows** this rule.

The `manifest.json` file for the `nest` integration includes a `codeowners` field:

```json
{
  "domain": "nest",
  "name": "Google Nest",
  "after_dependencies": ["media_source"],
  "codeowners": ["@allenporter"],
  "config_flow": true,
  "dependencies": ["ffmpeg", "http", "application_credentials"],
  "dhcp": [
    {
      "macaddress": "18B430*"
    },
    {
      "macaddress": "641666*"
    },
    {
      "macaddress": "D8EB46*"
    }
  ],
  "documentation": "https://www.home-assistant.io/integrations/nest",
  "iot_class": "cloud_push",
  "loggers": ["google_nest_sdm"],
  "requirements": ["google-nest-sdm==7.1.4"]
}
```

Specifically, the line `"codeowners": ["@allenporter"],` indicates that `@allenporter` is designated as the code owner for this integration. This satisfies the requirements of the `integration-owner` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 22:57:12. Prompt tokens: 32240, Output tokens: 462, Total tokens: 33242_
