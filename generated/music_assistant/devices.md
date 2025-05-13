# music_assistant: devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/devices)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `devices` rule applies to the `music_assistant` integration because it represents Music Assistant players as distinct devices within Home Assistant. Each player managed by Music Assistant is exposed as a `media_player` entity, and these entities should be grouped under a Home Assistant device to provide a clear and organized representation for the user.

The integration currently **partially** follows the rule. It successfully creates devices for each Music Assistant player using `DeviceInfo` in the `MusicAssistantEntity` class, located in `homeassistant/components/music_assistant/entity.py`.

Specifically, the `__init__` method of `MusicAssistantEntity` populates `_attr_device_info` with:
*   `identifiers`: `{(DOMAIN, player_id)}`
*   `manufacturer`: `self.player.device_info.manufacturer` or the provider name.
*   `model`: `self.player.device_info.model` or the player name.
*   `name`: `self.player.display_name`.
*   `configuration_url`: A direct link to the player's settings in Music Assistant.

This provides a good baseline of device information. However, the rule emphasizes that "the information about the device should be as complete as possible." The `music-assistant-models` library, specifically the `PlayerDeviceInfo` class, includes an `address` field (commented as "e.g. mac address or ip address"). This information could be used to populate the `connections` attribute of Home Assistant's `DeviceInfo`, which is a common and useful piece of information for identifying and troubleshooting devices. Currently, the `music_assistant` integration does not utilize this `address` field for the `connections` set.

Fields like `serial_number`, `hw_version`, or `sw_version` (for the player device itself, not the MA server) do not appear to be available in the `PlayerDeviceInfo` model provided by `music-assistant-models`, so their absence in the HA `DeviceInfo` is understandable. The primary point of non-compliance is the omission of `connections` when data for it (the `address`) might be available.

## Suggestions

To fully comply with the rule by making the device information "as complete as possible" with the available data, the integration should utilize the `player.device_info.address` field to populate the `connections` attribute in `DeviceInfo`.

1.  **Modify `MusicAssistantEntity.__init__` in `homeassistant/components/music_assistant/entity.py`:**
    Import necessary constants from `homeassistant.helpers.device_registry`:
    ```python
    from homeassistant.helpers.device_registry import (
        CONNECTION_NETWORK_MAC,
        CONNECTION_IP,
        DeviceInfo,
    )
    ```
    Or, if `dr` is already imported:
    ```python
    import homeassistant.helpers.device_registry as dr
    # Then use dr.CONNECTION_NETWORK_MAC, dr.CONNECTION_IP
    ```

2.  **Update the `DeviceInfo` instantiation to include `connections`:**
    ```python
    # In MusicAssistantEntity.__init__
    # ... (existing code) ...
    
    connections = set()
    if self.player.device_info.address:
        addr = self.player.device_info.address
        # Heuristic check for MAC vs IP. More robust parsing might be desired
        # if the format of 'address' isn't strictly one or the other.
        if ":" in addr and addr.count(":") == 5:  # Basic MAC address check
            connections.add((CONNECTION_NETWORK_MAC, addr.upper()))
        elif "." in addr and addr.count(".") == 3:  # Basic IPv4 address check
            # Ensure it's a valid IP if more advanced validation is needed
            connections.add((CONNECTION_IP, addr))
        # Add other connection types if MA could provide them and HA supports them

    self._attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, player_id)},
        manufacturer=self.player.device_info.manufacturer or provider.name,
        model=self.player.device_info.model or self.player.name,
        name=self.player.display_name,
        configuration_url=f"{mass.server_url}/#/settings/editplayer/{player_id}",
        connections=connections if connections else None, # Use None if set is empty
    )
    ```

**Why these changes satisfy the rule:**

*   By adding the `connections` data, the `DeviceInfo` becomes more complete, aligning better with the rule's requirement that "the information about the device should be as complete as possible."
*   Network connection identifiers (like MAC or IP addresses) are standard pieces of device information in Home Assistant and are valuable for users for identification and network management purposes.
*   This utilizes data already available from the `music-assistant-models` library (`player.device_info.address`) that is currently being overlooked for this purpose.

_Created at 2025-05-13 10:15:06. Prompt tokens: 30097, Output tokens: 1213, Total tokens: 37479_
