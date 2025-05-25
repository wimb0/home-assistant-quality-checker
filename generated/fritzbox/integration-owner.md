```markdown
# fritzbox: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner) |
| Status | **done**                                                                 |

## Overview

The `integration-owner` rule requires an integration to define its codeowners in the `manifest.json` file using the `codeowners` key, listing GitHub usernames prefixed with `@`. This rule applies to all integrations, and there are no exceptions.

The `fritzbox` integration includes a `manifest.json` file that defines the integration's metadata. Upon reviewing the `homeassistant/components/fritzbox/manifest.json` file, it contains the required `codeowners` key with a list of valid GitHub usernames:

```json
{
  "domain": "fritzbox",
  "name": "AVM FRITZ!SmartHome",
  "codeowners": ["@mib1185", "@flabbamann"],
  ...
}
```

This correctly implements the rule by specifying individuals responsible for maintaining the integration. Therefore, the integration fully follows the `integration-owner` rule.

## Suggestions

No suggestions needed. The integration already complies with this rule.
```

_Created at 2025-05-25 11:34:39. Prompt tokens: 18871, Output tokens: 325, Total tokens: 19564_
