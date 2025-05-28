```markdown
# samsungtv: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **done**                                       |
| Reason | |

## Overview

This rule requires integrations that poll devices or services to do so at an appropriate interval, using the `update_interval` parameter in a `DataUpdateCoordinator` or the `SCAN_INTERVAL` constant for entities with `should_poll = True`.

The `samsungtv` integration uses a `DataUpdateCoordinator` (`SamsungTVDataUpdateCoordinator` in `coordinator.py`) to handle data fetching. The `__init__` method of this coordinator explicitly sets the `update_interval`:

```python
super().__init__(
    hass,
    LOGGER,
    config_entry=config_entry,
    name=DOMAIN,
    update_interval=timedelta(seconds=SCAN_INTERVAL),
)
```

The `SCAN_INTERVAL` constant is defined in `coordinator.py` as `10`. Therefore, the integration polls the Samsung TV every 10 seconds.

The main purpose of this polling is to check the power state of the TV (`self.is_on = await self.bridge.async_is_on()` in `_async_update_data`). The TV's power state can change relatively often, and user feedback on this state is important for usability. A 10-second interval provides a reasonable balance between responsiveness to power state changes and avoiding excessive load on the device and the Home Assistant instance.

While the coordinator update also triggers `async_extra_update` which handles UPnP subscriptions and app list requests, the core state being polled every 10 seconds is the power state. Volume and mute states, when UPnP is available, are handled via push notifications after an initial subscription, further reducing the data polled frequently.

The integration correctly implements polling via a `DataUpdateCoordinator` and sets a defined `update_interval` based on a constant. The chosen interval of 10 seconds is considered appropriate for monitoring a media player's power state.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:27:47. Prompt tokens: 30287, Output tokens: 522, Total tokens: 31568_
