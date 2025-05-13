# music_assistant: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **done**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `config-entry-unloading` rule requires that integrations implement the `async_unload_entry` function to clean up all resources, subscriptions, and connections that were established during the `async_setup_entry` phase. This allows Home Assistant to unload the integration at runtime without needing a restart.

The `music_assistant` integration uses config entries, as indicated by `"config_flow": true` in its `manifest.json`. Therefore, this rule applies.

The integration correctly implements the `async_unload_entry` function in `homeassistant/components/music_assistant/__init__.py`. This function performs the following cleanup actions:

1.  **Unloads Platforms:** It calls `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` to ensure that any entities or platform-specific setups (in this case, for the `media_player` platform) are properly unloaded.
    ```python
    # homeassistant/components/music_assistant/__init__.py
    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Unload a config entry."""
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        # ...
    ```

2.  **Cleans Up Custom Resources (if platform unload is successful):**
    *   **Cancels Background Task:** The `listen_task`, which is an `asyncio.Task` created in `async_setup_entry` to listen to the Music Assistant client, is cancelled:
        ```python
        # homeassistant/components/music_assistant/__init__.py
        if unload_ok:
            mass_entry_data: MusicAssistantEntryData = entry.runtime_data
            mass_entry_data.listen_task.cancel()
            # ...
        ```
    *   **Disconnects Client:** The `MusicAssistantClient` connection (`mass_entry_data.mass`) is disconnected:
        ```python
        # homeassistant/components/music_assistant/__init__.py
            await mass_entry_data.mass.disconnect()
        ```

3.  **Handles Listeners via `entry.async_on_unload`:**
    During `async_setup_entry`, the integration registers two listeners using `entry.async_on_unload`:
    *   A listener for `EVENT_HOMEASSISTANT_STOP`:
        ```python
        # homeassistant/components/music_assistant/__init__.py
        entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_hass_stop)
        )
        ```
    *   A subscription to `EventType.PLAYER_REMOVED` events from the `MusicAssistantClient`:
        ```python
        # homeassistant/components/music_assistant/__init__.py
        entry.async_on_unload(
            mass.subscribe(handle_player_removed, EventType.PLAYER_REMOVED)
        )
        ```
    The `entry.async_on_unload` mechanism ensures that the unsubscription callables returned by `hass.bus.async_listen_once` and `mass.subscribe` are automatically executed when the config entry is unloaded successfully, or if `async_setup_entry` fails. This correctly cleans up these specific listeners.

The `async_unload_entry` function returns the result of `async_unload_platforms`, adhering to the requirement that it should return `True` for a successful unload and `False` otherwise. The custom resource cleanup is conditional on the success of platform unloading, which is a common and correct pattern.

All significant resources established in `async_setup_entry` (client connection, background task, event listeners, platforms) appear to be properly cleaned up either directly within `async_unload_entry` or through `entry.async_on_unload`.

Therefore, the `music_assistant` integration fully follows the `config-entry-unloading` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:09:05. Prompt tokens: 30139, Output tokens: 1026, Total tokens: 37156_
