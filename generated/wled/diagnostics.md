# wled: diagnostics

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [diagnostics](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `diagnostics` rule requires integrations to implement a way for users to gather data about the integration for debugging purposes, ensuring that no sensitive information is exposed.

The `wled` integration **applies** to this rule as it is a device integration that sets up a config entry.

The integration **fully follows** this rule.
It implements diagnostics support in the `diagnostics.py` file, providing the `async_get_config_entry_diagnostics` function as required.

Specifically:
1.  The file `diagnostics.py` exists.
2.  It contains the function `async_get_config_entry_diagnostics(hass: HomeAssistant, entry: WLEDConfigEntry) -> dict[str, Any]`.
3.  This function returns a dictionary containing various pieces of information about the WLED device and its state, including:
    *   Device information (`info`)
    *   Current state (`state`)
    *   Lists of effects, palettes, playlists, and presets.
4.  Sensitive information is handled:
    *   The `info` dictionary, which is derived from `coordinator.data.info.to_dict()`, has its `wifi` key redacted using `async_redact_data`. This is important as Wi-Fi details (like SSID or BSSID) could be considered sensitive.
    *   The WLED integration's config entry data (`entry.data`) only stores the host of the WLED device. The diagnostics function does not explicitly include `entry.data`, but focuses on the runtime data from the coordinator. The host/IP is generally not considered sensitive in the context of local network devices to the same degree as API keys or passwords, and the rule example does not show redaction of host information from `entry.data`.

The provided diagnostics data is comprehensive and useful for debugging, while also taking precautions to redact potentially sensitive network information.

```python
# diagnostics.py
async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: WLEDConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    data: dict[str, Any] = {
        "info": async_redact_data(coordinator.data.info.to_dict(), "wifi"), # Redaction of wifi info
        "state": coordinator.data.state.to_dict(),
        "effects": {
            effect.effect_id: effect.name
            for effect in coordinator.data.effects.values()
        },
        "palettes": {
            palette.palette_id: palette.name
            for palette in coordinator.data.palettes.values()
        },
        "playlists": {
            playlist.playlist_id: playlist.name
            for playlist in coordinator.data.playlists.values()
        },
        "presets": {
            preset.preset_id: preset.name
            for preset in coordinator.data.presets.values()
        },
    }
    return data
```

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:58:12. Prompt tokens: 20679, Output tokens: 788, Total tokens: 23673_
