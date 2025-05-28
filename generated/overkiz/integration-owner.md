# overkiz: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `integration-owner` rule applies to the `overkiz` integration. This rule requires that integrations specify at least one code owner in their `manifest.json` file. This practice helps in maintaining the integration by assigning responsibility and ensuring that there's a designated person to handle issues and pull requests.

The `overkiz` integration fully complies with this rule. The `manifest.json` file for the integration, located at `homeassistant/components/overkiz/manifest.json`, includes the `codeowners` field.

Specifically, the `manifest.json` contains:
```json
{
  "domain": "overkiz",
  "name": "Overkiz",
  "codeowners": ["@imicknl"],
  ...
}
```
The presence of `"codeowners": ["@imicknl"]` clearly designates `@imicknl` as the code owner for the `overkiz` integration, thereby satisfying the rule's requirements.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:21:02. Prompt tokens: 86880, Output tokens: 336, Total tokens: 88196_
