```markdown
# samsungtv: integration-owner

| Info   | Value                                                                                                |
|--------|------------------------------------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/)                                   |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner) |
| Status | **done**                                                                                             |

## Overview

The `integration-owner` rule requires that an integration's `manifest.json` file includes a `"codeowners"` key listing the GitHub usernames of the integration's maintainers.

This rule applies to the `samsungtv` integration. Upon reviewing the `homeassistant/components/samsungtv/manifest.json` file, the `"codeowners"` key is present and contains a list of GitHub usernames:

```json
{
  "domain": "samsungtv",
  "name": "Samsung Smart TV",
  "codeowners": ["@chemelli74", "@epenet"],
  ...
}
```

The presence of this field with valid entries indicates that the integration adheres to the `integration-owner` rule.

## Suggestions

No suggestions needed. The integration follows the rule.
```

_Created at 2025-05-25 11:30:11. Prompt tokens: 30014, Output tokens: 289, Total tokens: 30644_
