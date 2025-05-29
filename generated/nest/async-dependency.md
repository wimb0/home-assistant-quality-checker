# nest: async-dependency

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [async-dependency](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/async-dependency)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `async-dependency` rule requires that the external libraries used by an integration are asyncio-based to ensure efficient operation within Home Assistant's asynchronous environment and to maintain clean code.

This rule applies to the `nest` integration as it utilizes the `google-nest-sdm` library (specified in `manifest.json` as `requirements: ["google-nest-sdm==7.1.4"]`).

The `nest` integration fully follows this rule. The `google-nest-sdm` library is designed to be asynchronous, and the integration interacts with it using `async/await` patterns throughout its codebase.

Key indicators of the library's asynchronous nature and the integration's compliance include:

1.  **Asynchronous Library Methods:** The integration consistently `await`s calls to methods from the `google-nest-sdm` library. This is evident in multiple files:
    *   In `homeassistant/components/nest/__init__.py`:
        *   `auth = await api.new_auth(hass, entry)` which internally uses library components.
        *   `await auth.async_get_access_token()` (a method from an auth object provided by the library via `api.py`).
        *   `subscriber = await api.new_subscriber(hass, entry, auth)`.
        *   `unsub = await subscriber.start_async()`.
        *   `device_manager = await subscriber.async_get_device_manager()`.
        *   Event media fetching: `await nest_device.event_media_manager.get_media_from_token(...)` and `await nest_device.event_media_manager.get_clip_thumbnail_from_token(...)` in `NestEventViewBase` subclasses.
    *   In `homeassistant/components/nest/api.py`:
        *   The `AsyncConfigEntryAuth` class, which inherits from the library's `AbstractAuth`, implements `async def async_get_access_token()` and `async def async_get_creds()`. These methods are expected by the library to be asynchronous.
        *   `GoogleNestSubscriber` and `AdminClient` from the library are initialized with an `aiohttp.ClientSession` and an `AbstractAuth` implementation that is async.
    *   In `homeassistant/components/nest/camera.py`:
        *   `await self._rtsp_live_stream_trait.generate_rtsp_stream()`.
        *   `await self._rtsp_stream.extend_rtsp_stream()`.
        *   `await trait.generate_web_rtc_stream(offer_sdp)`.
        *   `await webrtc_stream.extend_stream()`.
        *   `await stream.stop_stream()`.
    *   In `homeassistant/components/nest/climate.py`:
        *   Various trait methods like `await trait.set_mode(...)`, `await trait.set_range(...)`, `await trait.set_heat(...)`, etc., are all awaited.
    *   In `homeassistant/components/nest/config_flow.py`:
        *   `await self._admin_client.create_topic(...)`, `await self._admin_client.list_eligible_topics(...)`, `await self._admin_client.create_subscription(...)`.
        *   `await subscriber.async_get_device_manager()`.
    *   In `homeassistant/components/nest/media_source.py`:
        *   `await device.event_media_manager.async_clip_preview_sessions()`
        *   `await device.event_media_manager.async_image_sessions()`

2.  **Asynchronous Callbacks:** The `SignalUpdateCallback` in `__init__.py` defines an `async def async_handle_event` method, which is passed to `subscriber.set_update_callback()`. This implies the library's subscriber expects and handles asynchronous callbacks.

3.  **Use of `aiohttp`:** The library implicitly (and the integration explicitly when setting up auth objects in `api.py`) uses `aiohttp` for HTTP communication, which is an asynchronous HTTP client/server framework. This is evidenced by passing `aiohttp_client.async_get_clientsession(hass)` to library components.

These patterns demonstrate that `google-nest-sdm` is an asyncio-based library, and the `nest` integration correctly uses it in an asynchronous manner, thereby complying with the `async-dependency` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:17:48. Prompt tokens: 32046, Output tokens: 1113, Total tokens: 35342_
