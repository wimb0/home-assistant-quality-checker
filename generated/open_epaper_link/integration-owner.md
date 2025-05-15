# open_epaper_link: integration-owner

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [integration-owner](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/integration-owner)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `integration-owner` rule applies to all Home Assistant integrations. This rule mandates that the integration's `manifest.json` file includes a `codeowners` field, which should be a list containing at least one GitHub username. This ensures that there is a designated person responsible for the stewardship and maintenance of the integration.

The `open_epaper_link` integration fully adheres to this rule. The provided `homeassistant/components/open_epaper_link/manifest.json` file includes the required `codeowners` field.

Specifically, the `manifest.json` contains:
```json
{
  "domain": "open_epaper_link",
  "name": "OpenEPaperLink",
  "codeowners": [
    "@jonasniesner"
  ],
  "config_flow": true,
  "dependencies": [
    "recorder"
  ],
  "documentation": "https://github.com/jonasniesner/open_epaper_link_homeassistant",
  "integration_type": "hub",
  "iot_class": "local_push",
  "issue_tracker": "https://github.com/jonasniesner/open_epaper_link_homeassistant/issues",
  "requirements": [
    "qrcode[pil]==7.4.2",
    "requests_toolbelt==1.0.0",
    "websocket-client==1.7.0",
    "websockets==14.2"
  ],
  "single_config_entry": true,
  "version": "1.0.0"
}
```
As highlighted, the `codeowners` field is present and correctly lists `["@jonasniesner"]`. This fulfills the requirement of having at least one integration owner specified.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 20:50:03. Prompt tokens: 60369, Output tokens: 532, Total tokens: 61920_
