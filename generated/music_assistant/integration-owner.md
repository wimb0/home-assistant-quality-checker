# music_assistant: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `integration-owner` rule mandates that an integration must specify at least one owner in its `manifest.json` file. This is done by including a `"codeowners"` field with a list of GitHub usernames. This practice helps in maintaining the integration by ensuring that there are designated individuals responsible for its stewardship, who will be notified of issues and pull requests related to the integration.

The `music_assistant` integration **applies** to this rule, as there are no exceptions.

The integration **fully follows** this rule. The `manifest.json` file for `music_assistant` includes the `codeowners` field, and it specifies a code owner.

Specifically, the `homeassistant/components/music_assistant/manifest.json` file contains the following:
```json
{
  "domain": "music_assistant",
  "name": "Music Assistant",
  "after_dependencies": ["media_source", "media_player"],
  "codeowners": ["@music-assistant"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/music_assistant",
  "iot_class": "local_push",
  "loggers": ["music_assistant"],
  "requirements": ["music-assistant-client==1.2.0"],
  "zeroconf": ["_mass._tcp.local."]
}
```
The presence of `"codeowners": ["@music-assistant"]` confirms compliance with the rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:09:56. Prompt tokens: 29995, Output tokens: 452, Total tokens: 30924_
