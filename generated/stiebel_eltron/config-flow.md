# stiebel_eltron: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `config-flow` rule requires integrations to be configurable through the Home Assistant user interface. This involves having a `config_flow.py` file, setting `config_flow: true` in the `manifest.json`, using `strings.json` for localizable text (including `data_description` for clarity), validating user input, and correctly storing configuration in `ConfigEntry.data` (for connection parameters) and `ConfigEntry.options` (for other settings).

The `stiebel_eltron` integration **applies** to this rule because it requires user-provided configuration (host and port) to connect to a device.

The integration **fully follows** this rule:

1.  **`manifest.json`**:
    *   The `homeassistant/components/stiebel_eltron/manifest.json` file correctly includes `"config_flow": true`.

2.  **`config_flow.py`**:
    *   The integration has a `homeassistant/components/stiebel_eltron/config_flow.py` file.
    *   It defines `StiebelEltronConfigFlow` which inherits from `config_entries.ConfigFlow`.
    *   The `async_step_user` method is implemented to guide the user through setup:
        *   It presents a form requesting `CONF_HOST` and `CONF_PORT`.
        *   It validates the user input by attempting to connect to the Stiebel Eltron device using `StiebelEltronAPI(...).update()`.
        *   If the connection fails, an appropriate error (`cannot_connect` or `unknown`) is shown to the user.
        *   On successful validation, it creates a config entry using `self.async_create_entry(title="Stiebel Eltron", data=user_input)`. The `user_input` contains `CONF_HOST` and `CONF_PORT`.

3.  **`strings.json`**:
    *   The `homeassistant/components/stiebel_eltron/strings.json` file provides translations for the config flow.
    *   Crucially, for the `user` step, it includes `data_description` for both `host` and `port`, explaining what each field represents:
        ```json
        "data_description": {
          "host": "The hostname or IP address of your Stiebel Eltron device.",
          "port": "The port of your Stiebel Eltron device."
        }
        ```
        This enhances user-friendliness.

4.  **Configuration Storage**:
    *   The rule specifies that connection-critical information should be stored in `ConfigEntry.data` and other settings in `ConfigEntry.options`.
    *   The `stiebel_eltron` integration collects `CONF_HOST` and `CONF_PORT`, both essential for establishing a connection. These are stored in `ConfigEntry.data`.
    *   The integration does not currently define or collect any other settings that would be suitable for `ConfigEntry.options` (e.g., polling interval). The device name is handled by the config entry's title, which is standard practice.

5.  **YAML Import**:
    *   The integration supports importing configurations from the legacy YAML setup.
    *   `__init__.py` contains logic in `async_setup` and `_async_import` to read the old YAML configuration, extract necessary details (host, port, name), and initiate the config flow with `source=SOURCE_IMPORT`.
    *   `config_flow.py` implements `async_step_import` to handle this, creating a config entry from the imported data.
    *   The integration also correctly raises an issue (`deprecated_yaml`) to inform users about the YAML configuration being removed and that their configuration has been imported.

The implementation adheres to the requirements and best practices for config flows outlined in the rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 14:55:26. Prompt tokens: 6405, Output tokens: 973, Total tokens: 11560_
