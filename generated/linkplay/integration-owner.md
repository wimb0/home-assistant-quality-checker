# linkplay: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `integration-owner` rule applies to all Home Assistant integrations and requires that at least one code owner is specified in the `manifest.json` file. This ensures that there is a designated maintainer responsible for the integration, who will be notified of issues and pull requests.

The `linkplay` integration fully adheres to this rule. The `manifest.json` file for the `linkplay` integration includes a `codeowners` field, which is correctly populated with a GitHub username.

Specifically, the `linkplay/manifest.json` file contains the following entry:
```json
{
  "domain": "linkplay",
  "name": "LinkPlay",
  "codeowners": ["@Velleman"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/linkplay",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "loggers": ["linkplay"],
  "requirements": ["python-linkplay==0.2.4"],
  "zeroconf": ["_linkplay._tcp.local."]
}
```
The presence of `"codeowners": ["@Velleman"]` clearly designates `@Velleman` as the code owner for this integration, satisfying the requirements of the `integration-owner` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 14:59:29. Prompt tokens: 10283, Output tokens: 418, Total tokens: 11696_
