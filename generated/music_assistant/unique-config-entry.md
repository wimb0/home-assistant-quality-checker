# music_assistant: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |

## Overview

The `unique-config-entry` rule applies to the `music_assistant` integration because it utilizes a configuration flow to guide users through the setup process, as indicated by `"config_flow": true` in its `manifest.json` file. The purpose of this rule is to prevent users from accidentally setting up the same device or service multiple times, which can lead to duplicated entities and other issues.

The `music_assistant` integration correctly follows this rule. It achieves this by assigning a unique identifier (`unique_id`) to each configuration entry, based on the `server_id` of the Music Assistant server instance being configured.

This is implemented in `homeassistant/components/music_assistant/config_flow.py` within both the manual setup and discovery flows:

1.  **Manual Setup (`async_step_user`)**:
    *   When a user provides the URL of a Music Assistant server, the integration attempts to fetch server information, which includes a `server_id`.
    *   This `server_id` is then used to set a unique ID for the config entry:
        ```python
        # homeassistant/components/music_assistant/config_flow.py
        self.server_info = await get_server_info(
            self.hass, user_input[CONF_URL]
        )
        await self.async_set_unique_id(
            self.server_info.server_id, raise_on_progress=False
        )
        ```
    *   After setting the unique ID, it checks if an entry with this ID already exists and aborts the flow if it does, preventing a duplicate setup:
        ```python
        # homeassistant/components/music_assistant/config_flow.py
        self._abort_if_unique_id_configured(
            updates={CONF_URL: self.server_info.base_url},
            reload_on_update=True,
        )
        ```

2.  **Zeroconf Discovery (`async_step_zeroconf`)**:
    *   When a Music Assistant server is discovered via Zeroconf, its `server_id` is extracted from the discovery properties.
    *   Similar to the manual flow, this `server_id` is used to set the unique ID and check for existing configurations:
        ```python
        # homeassistant/components/music_assistant/config_flow.py
        self.server_info = ServerInfoMessage.from_dict(discovery_info.properties)
        await self.async_set_unique_id(self.server_info.server_id)
        self._abort_if_unique_id_configured(
            updates={CONF_URL: self.server_info.base_url},
            reload_on_update=True,
        )
        ```

By using the `server_id` obtained from the Music Assistant server as the `unique_id` for the config entry and employing `self.async_set_unique_id()` along with `self._abort_if_unique_id_configured()`, the integration ensures that each unique Music Assistant server can only be configured once. This aligns perfectly with the requirements of the `unique-config-entry` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:06:14. Prompt tokens: 30741, Output tokens: 826, Total tokens: 34172_
