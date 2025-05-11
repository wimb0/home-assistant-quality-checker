# wled: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration/quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `entity-unique-id` rule requires that all entities provided by an integration have a unique ID. This ID is crucial for Home Assistant to track entities across restarts, allowing users to customize them (e.g., rename, change entity ID, assign to areas). The unique ID must be unique per integration domain and per platform domain.

The `wled` integration defines entities across multiple platforms (button, light, number, select, sensor, switch, update). Each entity class within these platforms consistently sets the `_attr_unique_id` attribute during initialization.

The unique IDs are typically constructed using the WLED device's MAC address (obtained from `coordinator.data.info.mac_address`) combined with a suffix that uniquely identifies the entity within that device. This suffix can be:
*   A static string for entities that have only one instance per device (e.g., `_restart` for the restart button, or just the MAC address for the main light or update entity).
*   A key from an entity description for entities created from a list (e.g., sensor keys like `estimated_current`).
*   A segment ID for entities that are per-segment (e.g., segment lights, segment-specific numbers or switches).

This pattern ensures that each entity has a unique identifier that is stable across restarts and unique within the Home Assistant instance.

**Code evidence:**

*   **`button.py`:**
    *   `WLEDRestartButton.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_restart"
        ```
*   **`light.py`:**
    *   `WLEDMainLight.__init__`:
        ```python
        self._attr_unique_id = coordinator.data.info.mac_address
        ```
    *   `WLEDSegmentLight.__init__`:
        ```python
        self._attr_unique_id = (
            f"{self.coordinator.data.info.mac_address}_{self._segment}"
        )
        ```
*   **`number.py`:**
    *   `WLEDNumber.__init__`:
        ```python
        self._attr_unique_id = (
            f"{coordinator.data.info.mac_address}_{description.key}_{segment}"
        )
        ```
*   **`select.py`:**
    *   `WLEDLiveOverrideSelect.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_live_override"
        ```
    *   `WLEDPresetSelect.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_preset"
        ```
    *   `WLEDPlaylistSelect.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_playlist"
        ```
    *   `WLEDPaletteSelect.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_palette_{segment}"
        ```
*   **`sensor.py`:**
    *   `WLEDSensorEntity.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_{description.key}"
        ```
*   **`switch.py`:**
    *   `WLEDNightlightSwitch.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_nightlight"
        ```
    *   `WLEDSyncSendSwitch.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_sync_send"
        ```
    *   `WLEDSyncReceiveSwitch.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_sync_receive"
        ```
    *   `WLEDReverseSwitch.__init__`:
        ```python
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_reverse_{segment}"
        ```
*   **`update.py`:**
    *   `WLEDUpdateEntity.__init__`:
        ```python
        self._attr_unique_id = coordinator.data.info.mac_address
        ```

All entities created by the `wled` integration correctly implement unique IDs. Therefore, the integration adheres to the `entity-unique-id` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:27:36. Prompt tokens: 20918, Output tokens: 1174, Total tokens: 23563_
