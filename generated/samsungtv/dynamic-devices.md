```markdown
# samsungtv: dynamic-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [dynamic-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices)                                                     |
| Status | **exempt**                                       |
| Reason | The integration manages a single primary device (the TV) rather than a set of dynamic sub-devices or components. The entities represent the capabilities of this single device. |

## Overview

The `dynamic-devices` rule requires integrations to automatically create entities for new devices or components that appear after the initial setup of the integration. This is typically achieved by using a `DataUpdateCoordinator` that fetches a list of dynamic elements and adding entities for newly discovered ones via `async_add_entities`.

Based on the provided code, the `samsungtv` integration focuses on representing a single Samsung TV device configured via the config flow (`homeassistant/components/samsungtv/config_flow.py`). The integration discovers and sets up *one* device entry (`homeassistant/components/samsungtv/__init__.py`, `async_setup_entry`) which corresponds to the configured TV.

The `SamsungTVDataUpdateCoordinator` (`homeassistant/components/samsungtv/coordinator.py`) is used to fetch the `is_on` state and trigger updates for the entities associated with this *single* TV. The `media_player` (`homeassistant/components/samsungtv/media_player.py`) and `remote` (`homeassistant/components/samsungtv/remote.py`) platforms each set up *one* entity (`SamsungTVDevice` and `SamsungTVRemote`) tied to this specific config entry and device entry.

While a TV might have dynamic aspects like installed apps or UPnP/DLNA services, the current implementation incorporates these as attributes or sources of the main `media_player` entity (`homeassistant/components/samsungtv/media_player.py`, `_app_list_callback`, `_async_startup_dmr`, `_update_from_upnp`) rather than creating separate dynamic entities for each app or service.

Since the integration's architecture revolves around a single, static device (the TV itself) and its fixed set of capabilities represented by a few entities, rather than managing a collection of dynamic sub-devices or components that can appear or disappear, the `dynamic-devices` rule does not apply.

```
```

_Created at 2025-05-25 11:31:32. Prompt tokens: 30274, Output tokens: 565, Total tokens: 32018_
