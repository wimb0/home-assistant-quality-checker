# wled: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `appropriate-polling` rule requires that polling integrations set a polling interval that is appropriate for the device or service being polled, aiming to serve the majority of users without causing unnecessary load.

This rule applies to the `wled` integration because it utilizes `DataUpdateCoordinator` instances, which inherently involve a polling mechanism, even though the primary coordinator for device state (`WLEDDataUpdateCoordinator`) attempts to upgrade to a push-based WebSocket connection.

The `wled` integration follows this rule:

1.  **`WLEDDataUpdateCoordinator` (Device State & Control):**
    *   This coordinator is responsible for fetching the main state of the WLED device.
    *   It is initialized with `update_interval=SCAN_INTERVAL` as seen in `coordinator.py`:
        ```python
        # coordinator.py
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL, # SCAN_INTERVAL = timedelta(seconds=10)
        )
        ```
    *   `SCAN_INTERVAL` is defined in `const.py` as `timedelta(seconds=10)`.
    *   Crucially, this coordinator attempts to establish a WebSocket connection for real-time updates (`_use_websocket` method in `coordinator.py`). If the WebSocket is active, updates are pushed, and the scheduled polling via `_async_update_data` is effectively paused for device state.
    *   The 10-second polling interval primarily serves as:
        *   An initial data fetch upon setup.
        *   A mechanism to trigger the WebSocket connection attempt.
        *   A fallback mechanism if the WebSocket connection fails or is not supported by the WLED device.
    *   For a local, real-time device like WLED, where state changes can be frequent, a 10-second polling interval as a fallback is appropriate. It ensures that Home Assistant can still retrieve updates reasonably quickly if the preferred push mechanism is unavailable.

2.  **`WLEDReleasesDataUpdateCoordinator` (Firmware Releases):**
    *   This coordinator is responsible for checking for new WLED firmware releases.
    *   It is initialized with `update_interval=RELEASES_SCAN_INTERVAL` as seen in `coordinator.py`:
        ```python
        # coordinator.py
        super().__init__(
            hass,
            LOGGER,
            config_entry=None,
            name=DOMAIN,
            update_interval=RELEASES_SCAN_INTERVAL, # RELEASES_SCAN_INTERVAL = timedelta(hours=3)
        )
        ```
    *   `RELEASES_SCAN_INTERVAL` is defined in `const.py` as `timedelta(hours=3)`.
    *   Checking for firmware updates every 3 hours is a very appropriate interval. Firmware releases are infrequent, and this interval respects the source of this information (likely GitHub releases) by not polling excessively.

3.  **Entities:**
    *   All entities (lights, sensors, switches, etc.) in the `wled` integration are based on `CoordinatorEntity` and derive their state from one or both of these coordinators. They do not implement their own polling schedules using `SCAN_INTERVAL` at the entity platform level, correctly relying on the centralized coordinators. For example, `sensor.py` entities inherit from `WLEDEntity` which uses the `WLEDDataUpdateCoordinator`.

The `manifest.json` correctly identifies the integration with `"iot_class": "local_push"`, reflecting its primary intention to use WebSockets for device state updates. The polling mechanisms in place are sensible for initialization, fallback, and for data types (like firmware releases) that are inherently suited to polling.

Overall, the polling intervals are well-chosen: the device state polling is a reasonable fallback for a local push system, and the release checking poll is appropriately infrequent.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:24:40. Prompt tokens: 21958, Output tokens: 974, Total tokens: 26220_
