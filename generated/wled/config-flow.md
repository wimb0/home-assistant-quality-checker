# wled: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **done**                                                                 |
| Reason | (No reason needed as status is not "exempt")                             |

## Overview

The `config-flow` rule mandates that integrations must be configurable through the Home Assistant user interface. This involves creating a `config_flow.py` file, setting `config_flow: true` in `manifest.json`, using `strings.json` for UI text (including `data_description` for clarity), validating user input, and correctly storing configuration in `ConfigEntry.data` and settings in `ConfigEntry.options`.

The `wled` integration **applies** to this rule as it represents a device that users need to set up, and it does not fall under any exemptions listed in ADR-0010.

The integration **fully follows** this rule.

1.  **`config_flow.py` Implementation**:
    *   The integration includes a `config_flow.py` file, which defines `WLEDFlowHandler` for the main configuration flow and `WLEDOptionsFlowHandler` for managing integration options.
    *   The `async_step_user` method in `WLEDFlowHandler` correctly prompts the user for the WLED device's host (`CONF_HOST`).
    *   Input validation is performed in `async_step_user` by attempting to connect to the device using the `_async_get_device` helper. If a `WLEDConnectionError` occurs, an appropriate error (`cannot_connect`) is displayed to the user.
    *   The integration also supports discovery via `async_step_zeroconf`, providing a seamless setup experience for discoverable devices. It confirms the discovery with `async_step_zeroconf_confirm`.
    *   Unique ID handling is correctly implemented using the device's MAC address to prevent duplicate configurations (`await self.async_set_unique_id(...)`, `self._abort_if_unique_id_configured(...)`).

2.  **`manifest.json` Configuration**:
    *   The `manifest.json` file correctly sets `"config_flow": true`, enabling UI-based setup.

3.  **`strings.json` for UI Text and Clarity**:
    *   The `strings.json` file (and its translation `translations/en.json`) provides all necessary UI text for the config flow steps, including titles, descriptions, and error messages.
    *   Crucially, for the `user` step, it includes `data_description` for the `host` field:
        ```json
        "data_description": {
          "host": "Hostname or IP address of your WLED device."
        }
        ```
        This fulfills the requirement for providing context about input fields.

4.  **Configuration Storage**:
    *   Connection-critical information (`CONF_HOST`) is stored in `ConfigEntry.data`, as seen in `config_flow.py`:
        ```python
        return self.async_create_entry(
            title=device.info.name,
            data={
                CONF_HOST: user_input[CONF_HOST],
            },
        )
        ```
    *   Settings not essential for establishing the initial connection are handled via an options flow (`WLEDOptionsFlowHandler`) and stored in `ConfigEntry.options`. The `CONF_KEEP_MAIN_LIGHT` option is an example:
        ```python
        # config_flow.py (WLEDOptionsFlowHandler)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_KEEP_MAIN_LIGHT,
                        # ...
                    ): bool,
                }
            ),
        )
        ```
        This option is then correctly retrieved from `entry.options` in `coordinator.py`:
        ```python
        self.keep_main_light = entry.options.get(
            CONF_KEEP_MAIN_LIGHT, DEFAULT_KEEP_MAIN_LIGHT
        )
        ```

The `wled` integration demonstrates a comprehensive and correct implementation of the config flow, aligning with all requirements of the rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:25:21. Prompt tokens: 22518, Output tokens: 1012, Total tokens: 25609_
