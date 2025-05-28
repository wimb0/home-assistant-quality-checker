```markdown
# fritzbox: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling) |
| Status | **done**                                                                 |

## Overview

The `fritzbox` integration is identified as a `local_polling` integration in its `manifest.json`. This rule requires that polling integrations set an appropriate polling interval to avoid excessive requests.

The integration follows this rule by utilizing a `DataUpdateCoordinator` to manage data fetching and explicitly setting an `update_interval`.

Looking at `homeassistant/components/fritzbox/coordinator.py`, the `FritzboxDataUpdateCoordinator` is initialized with a specific update interval:

```python
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=config_entry.entry_id,
            update_interval=timedelta(seconds=30),
        )
```

The `update_interval` is set to `timedelta(seconds=30)`. For a local integration communicating with a Smart Home hub like the FRITZ!Box, a 30-second polling interval is generally considered appropriate. It provides reasonably fresh data for typical home automation scenarios involving switches, lights, and thermostats without excessively burdening the local network or the FRITZ!Box device itself.

The integration correctly implements the recommended pattern for polling using a `DataUpdateCoordinator` and defines a sensible default interval.

No suggestions needed.
```

_Created at 2025-05-25 11:19:43. Prompt tokens: 19144, Output tokens: 383, Total tokens: 20204_
