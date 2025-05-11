# wled: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `integration-owner` rule mandates that every integration should have at least one designated owner. This is specified in the `manifest.json` file through the `codeowners` field, which should contain a list of GitHub usernames. Having an integration owner ensures better maintenance, as they are automatically notified of issues and pull requests and are considered experts on the integration.

This rule applies to the `wled` integration, as there are no exceptions to this rule.

The `wled` integration **fully follows** this rule. The `manifest.json` file includes a `codeowners` field with a specified GitHub username.

Specifically, the `manifest.json` file contains:
```json
{
  "domain": "wled",
  "name": "WLED",
  "codeowners": ["@frenck"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/wled",
  "integration_type": "device",
  "iot_class": "local_push",
  "requirements": ["wled==0.21.0"],
  "zeroconf": ["_wled._tcp.local."]
}
```
The presence of `"codeowners": ["@frenck"]` indicates that an owner is defined for this integration.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:54:47. Prompt tokens: 20898, Output tokens: 411, Total tokens: 21859_
