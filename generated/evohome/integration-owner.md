# evohome: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                                                 |

## Overview

The `integration-owner` rule requires that an integration has at least one designated owner specified in its `manifest.json` file. This is crucial for maintenance, issue tracking, and ensuring a point of contact for the integration.

The rule applies to the `evohome` integration as it is a standard Home Assistant integration and is expected to have a `manifest.json` file declaring its metadata, including code owners.

The `evohome` integration **fully follows** this rule. The `manifest.json` file for the `evohome` integration includes the `codeowners` field, and it specifies a GitHub username.

Specifically, the file `homeassistant/components/evohome/manifest.json` contains the following:
```json
{
  "domain": "evohome",
  "name": "Honeywell Total Connect Comfort (Europe)",
  "codeowners": ["@zxdavb"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/evohome",
  "iot_class": "cloud_polling",
  "loggers": ["evohome", "evohomeasync", "evohomeasync2"],
  "quality_scale": "legacy",
  "requirements": ["evohome-async==1.0.5"],
  "single_config_entry": true
}
```
The presence of `"codeowners": ["@zxdavb"]` confirms that an owner is designated for this integration, satisfying the rule's requirements.

## Suggestions

No suggestions needed.

---

_Created at 2025-05-29 12:44:27. Prompt tokens: 21710, Output tokens: 457, Total tokens: 23308._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
