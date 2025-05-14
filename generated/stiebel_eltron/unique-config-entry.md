# stiebel_eltron: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |

## Overview

The `unique-config-entry` rule applies to the `stiebel_eltron` integration because it uses a configuration flow to set up devices, as indicated by `"config_flow": true` in its `manifest.json`. The rule requires that an integration prevents the same device or service from being set up multiple times to avoid duplicated entities and potential unique identifier collisions.

The `stiebel_eltron` integration correctly follows this rule by ensuring that each device, identified by its host and port, can only be configured once. This is achieved using the `_async_abort_entries_match` method within its config flow.

Specifically, in `config_flow.py`:

1.  In the `async_step_user` method, which handles manual user configuration, the following line is present:
    ```python
    self._async_abort_entries_match(
        {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
    )
    ```
    This code checks if a configuration entry already exists with the same `CONF_HOST` and `CONF_PORT` provided by the user. If a match is found, the flow is aborted, preventing a duplicate setup.

2.  Similarly, in the `async_step_import` method, which handles configuration import (e.g., from YAML), the same check is performed:
    ```python
    self._async_abort_entries_match(
        {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
    )
    ```
    This ensures that imported configurations also do not lead to duplicates if a device with the same host and port is already configured.

This implementation aligns with the "Unique data" approach described in the rule's documentation, where pieces of the configuration data (host and port in this case) are used to uniquely identify a device instance. The `strings.json` file also includes an `abort` reason for `"already_configured": "[%key:common::config_flow::abort::already_configured_device%]"` which is the standard message shown to the user in such cases.

Therefore, the `stiebel_eltron` integration effectively prevents the same device from being set up multiple times.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:01:49. Prompt tokens: 6738, Output tokens: 621, Total tokens: 9331_
