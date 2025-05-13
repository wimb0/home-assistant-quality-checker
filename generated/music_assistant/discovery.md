# music_assistant: discovery

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [discovery](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery)                                                     |
| Status | **done**                                       |

## Overview

The `discovery` rule applies to the `music_assistant` integration. Music Assistant is a server application that runs on the user's network and can announce its presence using mDNS (Zeroconf). Implementing discovery for such a service significantly improves the user experience by simplifying the setup process.

The integration fully follows this rule. It implements Zeroconf discovery, allowing Home Assistant to automatically find Music Assistant servers on the local network.

**Evidence of Compliance:**

1.  **Manifest Declaration:**
    The `homeassistant/components/music_assistant/manifest.json` file correctly declares the Zeroconf service type that Music Assistant servers announce:
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
    The `zeroconf: ["_mass._tcp.local."]` line instructs Home Assistant to listen for this specific mDNS service type.

2.  **Config Flow Implementation for Zeroconf:**
    The `homeassistant/components/music_assistant/config_flow.py` file implements the necessary methods to handle discovered services:
    *   **`async_step_zeroconf`:** This method is triggered when a `_mass._tcp.local.` service is discovered.
        ```python
        async def async_step_zeroconf(
            self, discovery_info: ZeroconfServiceInfo
        ) -> ConfigFlowResult:
            """Handle a discovered Mass server."""
            # ... (validation of discovery_info.properties)
            self.server_info = ServerInfoMessage.from_dict(discovery_info.properties)
            await self.async_set_unique_id(self.server_info.server_id)
            self._abort_if_unique_id_configured(
                updates={CONF_URL: self.server_info.base_url},
                reload_on_update=True,
            )
            try:
                await get_server_info(self.hass, self.server_info.base_url)
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")
            return await self.async_step_discovery_confirm()
        ```
        Key aspects of this method:
        *   It receives `ZeroconfServiceInfo`.
        *   It extracts necessary information (like `server_id` and `base_url`) from `discovery_info.properties` by constructing a `ServerInfoMessage`.
        *   It sets a unique ID using `await self.async_set_unique_id(self.server_info.server_id)` to prevent duplicate entries and to allow updates to existing entries if the URL changes.
        *   It uses `self._abort_if_unique_id_configured()` to handle already configured instances, correctly passing `updates` and `reload_on_update`.
        *   It verifies that a connection can be established to the discovered server via `get_server_info`.
        *   It proceeds to a confirmation step.

    *   **`async_step_discovery_confirm`:** This method allows the user to confirm the addition of the discovered server.
        ```python
        async def async_step_discovery_confirm(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            """Handle user-confirmation of discovered server."""
            if TYPE_CHECKING:
                assert self.server_info is not None
            if user_input is not None:
                return self.async_create_entry(
                    title=DEFAULT_TITLE,
                    data={
                        CONF_URL: self.server_info.base_url,
                    },
                )
            self._set_confirm_only()
            return self.async_show_form(
                step_id="discovery_confirm",
                description_placeholders={"url": self.server_info.base_url},
            )
        ```
        This step presents the discovered server's URL to the user and, upon confirmation, creates the configuration entry.

The implementation aligns with the best practices and examples provided for discovery in Home Assistant.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:16:33. Prompt tokens: 30694, Output tokens: 1146, Total tokens: 33934_
