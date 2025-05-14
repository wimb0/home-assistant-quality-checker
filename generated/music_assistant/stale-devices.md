# music_assistant: stale-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [stale-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/stale-devices)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `stale-devices` rule requires that devices removed from a hub or account are also removed from Home Assistant. If an integration can detect removed devices, it should remove them automatically. If not, it must implement `async_remove_config_entry_device` to allow manual removal, ensuring the device is indeed unavailable before allowing deletion.

The `music_assistant` integration manages "player" devices, which are entities controlled by a Music Assistant server. This rule is applicable as players can be removed or become unavailable on the Music Assistant server.

The integration correctly implements mechanisms to handle stale devices:

1.  **Automatic Removal During Setup:**
    In `__init__.py`, within the `async_setup_entry` function (lines 120-130), the integration fetches all current player configurations from the Music Assistant server (`await mass.config.get_player_configs()`). It then iterates through the devices registered in Home Assistant for this config entry and compares them against the list from the server. If a Home Assistant device (player) is not found in the server's list, it is removed using `dev_reg.async_update_device(device.id, remove_config_entry_id=entry.entry_id)`. This handles cases where devices might have been removed from the Music Assistant server while Home Assistant was offline or the integration was not running.

    ```python
    # __init__.py (lines 120-130)
    # check if any playerconfigs have been removed while we were disconnected
    all_player_configs = await mass.config.get_player_configs()
    player_ids = {player.player_id for player in all_player_configs}
    dev_reg = dr.async_get(hass)
    dev_entries = dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
    for device in dev_entries:
        for identifier in device.identifiers:
            if identifier[0] == DOMAIN and identifier[1] not in player_ids:
                dev_reg.async_update_device(
                    device.id, remove_config_entry_id=entry.entry_id
                )
    ```

2.  **Event-Driven Automatic Removal:**
    Also in `async_setup_entry` (lines 110-119), the integration subscribes to `EventType.PLAYER_REMOVED` events from the Music Assistant server. When a player is removed on the server, the `handle_player_removed` callback is triggered. This function then removes the corresponding device from Home Assistant's device registry using `dev_reg.async_update_device(hass_device.id, remove_config_entry_id=entry.entry_id)`. This ensures real-time cleanup of devices.

    ```python
    # __init__.py (lines 110-119)
    # register listener for removed players
    async def handle_player_removed(event: MassEvent) -> None:
        """Handle Mass Player Removed event."""
        if event.object_id is None:
            return
        dev_reg = dr.async_get(hass)
        if hass_device := dev_reg.async_get_device({(DOMAIN, event.object_id)}):
            dev_reg.async_update_device(
                hass_device.id, remove_config_entry_id=entry.entry_id
            )

    entry.async_on_unload(
        mass.subscribe(handle_player_removed, EventType.PLAYER_REMOVED)
    )
    ```

3.  **Manual Removal Support:**
    The integration implements `async_remove_config_entry_device` in `__init__.py` (lines 159-181). This function is called when a user tries to delete a device from the Home Assistant UI.
    *   It first checks if the player is still known to the Music Assistant server (`mass.players.get(player_id) is None`). If the player is not found on the server, it's considered orphaned, and the function returns `True`, allowing deletion.
    *   If the player still exists on the server, it attempts to remove the player configuration from the Music Assistant server itself (`await mass.config.remove_player_config(player_id)`).
        *   If this server-side removal is successful, the function returns `True`, allowing the device to be deleted from Home Assistant.
        *   If the server-side removal fails (e.g., due to `ActionUnavailable`), it returns `False`, preventing the deletion from Home Assistant if the device is still active or cannot be removed from the server.

    ```python
    # __init__.py (lines 159-181)
    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
    ) -> bool:
        """Remove a config entry from a device."""
        player_id = next(
            (
                identifier[1]
                for identifier in device_entry.identifiers
                if identifier[0] == DOMAIN
            ),
            None,
        )
        if player_id is None:
            return False
        mass = get_music_assistant_client(hass, config_entry.entry_id)
        if mass.players.get(player_id) is None:
            # player is already removed on the server, this is an orphaned device
            return True
        # try to remove the player from the server
        try:
            await mass.config.remove_player_config(player_id)
        except ActionUnavailable:
            return False
        else:
            return True
    ```

These mechanisms collectively ensure that stale devices are handled appropriately, both automatically and through user-initiated actions, in accordance with the rule's requirements.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 13:46:44. Prompt tokens: 30524, Output tokens: 1443, Total tokens: 34460_
