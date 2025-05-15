# open_epaper_link: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `unique-config-entry` rule mandates that an integration must prevent the same device or service from being set up multiple times. This is to avoid duplicated entities and potential unique identifier collisions.

This rule applies to the `open_epaper_link` integration as it uses a configuration flow to set up a connection to an OpenEPaperLink Access Point (AP).

The `open_epaper_link` integration **fully follows** this rule through two mechanisms:

1.  **`single_config_entry: true` in `manifest.json`**:
    The `manifest.json` file for the integration includes the line:
    ```json
    "single_config_entry": true
    ```
    This declaration informs Home Assistant core that the integration can only have one configuration entry active at any time. If a user attempts to add the `open_epaper_link` integration after one instance is already configured, Home Assistant will prevent the new setup flow from completing, effectively ensuring the "service" (the OpenEPaperLink hub integration itself) cannot be set up twice.

2.  **Unique ID check in `config_flow.py`**:
    The integration's configuration flow (`config_flow.py`) implements the recommended pattern of assigning and checking a unique ID for the config entry. Specifically, in the `async_step_user` method, the host of the AP is used as the unique identifier:
    ```python
    # homeassistant/components/open_epaper_link/config_flow.py
    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ):
        # ...
        if user_input is not None:
            info, error = await self._validate_input(user_input[CONF_HOST])
            if not error:
                await self.async_set_unique_id(self._host) # self._host is the sanitized AP host
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={CONF_HOST: self._host}
                )
        # ...
    ```
    The `await self.async_set_unique_id(self._host)` call assigns the AP's host as the unique ID for the configuration entry. The subsequent `self._abort_if_unique_id_configured()` call checks if an entry with this unique ID already exists. If it does (meaning the user is trying to add an AP with the same host address again), the flow is aborted. This prevents the *same specific device* (the AP at a particular host) from being configured multiple times.

While `single_config_entry: true` is the primary mechanism ensuring only one instance of the integration, the additional unique ID check within the config flow provides a further layer of robustness, particularly if the integration were to support discovery in the future or if `single_config_entry` was not set to `true`.

Together, these mechanisms ensure that the `open_epaper_link` integration cannot be set up multiple times, nor can the same AP be configured more than once, fully complying with the `unique-config-entry` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 20:42:19. Prompt tokens: 61115, Output tokens: 843, Total tokens: 66610_
