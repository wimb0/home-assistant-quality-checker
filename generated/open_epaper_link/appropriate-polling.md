# open_epaper_link: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **exempt**                                       |
| Reason | The integration is classified as `local_push` and primarily uses a WebSocket connection for receiving data updates from the device, not periodic polling for entity states. |

## Overview

The `appropriate-polling` rule states that if an integration is a polling integration, it must set an appropriate polling interval. This rule does **not apply** to the `open_epaper_link` integration because it is designed as a push-based integration.

1.  **IoT Class:** The integration's `manifest.json` declares its `iot_class` as `"local_push"`:
    ```json
    // homeassistant/components/open_epaper_link/manifest.json
    {
      "domain": "open_epaper_link",
      "name": "OpenEPaperLink",
      "iot_class": "local_push",
      // ...
    }
    ```
    This classification indicates that the integration primarily receives data initiated by the device/hub.

2.  **Update Mechanism:** The core of the integration, found in `homeassistant/components/open_epaper_link/hub.py`, utilizes a WebSocket connection to receive real-time updates from the OpenEPaperLink Access Point (AP).
    The `Hub` class's `_websocket_handler` method establishes and maintains this connection:
    ```python
    // homeassistant/components/open_epaper_link/hub.py
    async def _websocket_handler(self) -> None:
        # ...
        async with self._session.ws_connect(ws_url, heartbeat=30) as ws:
            self.online = True
            # ...
            while not self._shutdown.is_set():
                try:
                    msg = await ws.receive() # Receives pushed messages
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle_message(msg.data)
                    # ...
                # ...
    ```
    Incoming messages are processed by `_handle_message` and then dispatched to relevant entities using `async_dispatcher_send`.

3.  **Entity Updates:** Entities, such as sensors defined in `homeassistant/components/open_epaper_link/sensor.py`, subscribe to these dispatched signals. They do not implement polling mechanisms like `SCAN_INTERVAL` or use a `DataUpdateCoordinator` with an `update_interval` for their primary state updates. Instead, they rely on `async_dispatcher_connect` in their `async_added_to_hass` method:
    ```python
    // homeassistant/components/open_epaper_link/sensor.py
    # In OpenEPaperLinkTagSensor
    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_tag_update_{self._tag_mac}", # Listens for pushed updates
                self._handle_update,
            )
        )
    ```
    This pattern is consistent across other entity platforms within the integration.

4.  **Ancillary Data Fetching:** The `TagTypesManager` in `homeassistant/components/open_epaper_link/tag_types.py` does fetch tag type definitions from GitHub. This fetch occurs if data is not cached or if the cache is older than `CACHE_DURATION` (48 hours).
    ```python
    // homeassistant/components/open_epaper_link/tag_types.py
    class TagTypesManager:
        # ...
        CACHE_DURATION = timedelta(hours=48)
        # ...
        async def ensure_types_loaded(self) -> None:
            # ...
            if (not self._last_update or
                  datetime.now() - self._last_update > CACHE_DURATION):
                await self._fetch_tag_types()
    ```
    This periodic fetching is for metadata (hardware definitions) rather than real-time entity states. A 48-hour interval for such metadata is very conservative. This mechanism does not classify the entire integration as a "polling integration" in the context of the `appropriate-polling` rule, which primarily concerns the polling of device/service states for entity updates.

Given that the primary mechanism for receiving updates about tags and AP status is push-based via WebSockets, the `open_epaper_link` integration is not considered a polling integration for the purpose of this rule. Thus, the rule is exempt.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 20:32:43. Prompt tokens: 60642, Output tokens: 1118, Total tokens: 65494_
