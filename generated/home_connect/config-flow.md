# home_connect: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `config-flow` rule mandates that integrations must be configurable through the Home Assistant user interface via a config flow. This includes having a `config_flow.py` file, setting `config_flow: true` in `manifest.json`, and providing UI text in `strings.json`.

The `home_connect` integration **complies** with this rule.

1.  **`manifest.json`**:
    *   The `manifest.json` file correctly sets `"config_flow": true`.
    ```json
    {
      "domain": "home_connect",
      "name": "Home Connect",
      ...
      "config_flow": true,
      ...
    }
    ```

2.  **`config_flow.py`**:
    *   The integration includes a `config_flow.py` file.
    *   This file implements `OAuth2FlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN)`, which is the standard and correct way to handle OAuth2-based authentication flows in Home Assistant. This allows users to authorize Home Assistant to access their Home Connect account via the Home Connect portal.
    *   The flow correctly handles `async_oauth_create_entry` to store the OAuth token in `ConfigEntry.data` and sets a unique ID.
    *   It also implements `async_step_reauth` and `async_step_reauth_confirm` for handling re-authentication.

3.  **`strings.json`**:
    *   The `strings.json` (and its translation `translations/en.json`) file is present and contains the necessary text for the config flow UI. Specifically, it includes entries for:
        *   `config.step.pick_implementation`: For the standard OAuth flow step.
        *   `config.step.reauth_confirm`: For guiding the user through re-authentication, including a title and description.
        *   `config.abort`: For various abort scenarios during the OAuth flow.
        *   `config.create_entry`: For confirming successful authentication.
    ```json
    // strings.json excerpt
    "config": {
      "step": {
        "pick_implementation": {
          "title": "[%key:common::config_flow::title::oauth2_pick_implementation%]"
        },
        "reauth_confirm": {
          "title": "[%key:common::config_flow::title::reauth%]",
          "description": "The Home Connect integration needs to re-authenticate your account"
        }
      },
      "abort": {
        "already_configured": "[%key:common::config_flow::abort::already_configured_account%]",
        "reauth_successful": "[%key:common::config_flow::abort::reauth_successful%]",
        // ... other abort reasons
      },
      "create_entry": {
        "default": "[%key:common::config_flow::create_entry::authenticated%]"
      }
    }
    ```

4.  **User-friendliness**:
    *   The integration uses the standard Home Assistant OAuth2 flow, which is a well-understood and user-friendly pattern for cloud-based services requiring external authentication.
    *   The rule's mention of "right selectors" and `data_description` for input fields primarily applies to flows that present custom forms within Home Assistant. For an OAuth2 flow like Home Connect's, user credential input occurs on the external Home Connect portal, not within a Home Assistant form defined by `data_schema`. The provided `strings.json` handles the HA-side prompts appropriately.

5.  **Configuration Storage**:
    *   As per the rule, "The integration should store all configuration in the `ConfigEntry.data` field". The `OAuth2FlowHandler` stores the obtained OAuth token (essential connection information) in `ConfigEntry.data`, which is correct. There are no user-configurable settings during the initial setup that would necessitate the use of `ConfigEntry.options` at this stage.

6.  **Exemptions**:
    *   The `home_connect` integration is not exempt under ADR-0010 as it is a user-facing cloud integration requiring explicit setup.

The integration fulfills all requirements to be set up via the UI using a config flow.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 20:18:34. Prompt tokens: 140375, Output tokens: 1083, Total tokens: 143977_
