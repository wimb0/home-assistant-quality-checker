# linkplay: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `appropriate-polling` rule requires that polling integrations set an appropriate polling interval to balance data freshness with system and network load. This interval should serve the majority of users, who can customize it if needed.

The `linkplay` integration is identified as a `local_polling` integration in its `manifest.json`. This means the rule applies.

The integration primarily involves `LinkPlayMediaPlayerEntity` entities, which poll for state updates. This is evident in `media_player.py`:
1.  The `LinkPlayMediaPlayerEntity` class implements an `async_update` method, which means its `should_poll` attribute will default to `True`.
2.  A `SCAN_INTERVAL` is explicitly defined at the module level:
    ```python
    # media_player.py
    SCAN_INTERVAL = timedelta(seconds=5)
    ```
    This sets the polling interval for all `LinkPlayMediaPlayerEntity` instances to 5 seconds.

For a local media player integration like `linkplay`, a 5-second polling interval is generally considered appropriate. Media player states (e.g., play/pause, volume, current track, playback position) can change frequently, and users typically expect Home Assistant to reflect these changes in a timely manner for responsive UI and automations. A 5-second interval strikes a reasonable balance between responsiveness and resource usage for local devices.

The other entities provided by this integration are `LinkPlayButton` entities (`button.py`). These inherit from `ButtonEntity`, which has `_attr_should_poll` defaulting to `False`. Buttons are typically action-oriented and do not require periodic polling for their state, so no `SCAN_INTERVAL` is needed or set for them, which is correct.

The integration uses the entity-specific `SCAN_INTERVAL` method for polling, which is one of the two mechanisms described by the rule documentation. It has consciously set an interval rather than relying on potentially less suitable defaults.

Therefore, the `linkplay` integration follows the `appropriate-polling` rule by defining a specific and arguably appropriate polling interval for its main polling entities.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:08:16. Prompt tokens: 11370, Output tokens: 567, Total tokens: 14165_
