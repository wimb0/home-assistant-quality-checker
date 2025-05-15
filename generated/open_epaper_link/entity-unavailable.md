# open_epaper_link: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **todo**                                                                 |

## Overview

The `entity-unavailable` rule requires that entities accurately reflect their availability status. If an integration cannot fetch data from a device or service, its entities should be marked as unavailable.

This rule applies to the `open_epaper_link` integration as it involves communication with a central Access Point (AP) and individual E-Paper tags. The availability of these entities is dependent on the connection status to the AP and, for tag-specific entities, the status of the individual tag as reported by the AP.

The integration's `Hub` class (`hub.py`) correctly manages an `online` status for the AP and dispatches a `f"{DOMAIN}_connection_status"` signal when this status changes.

Several entity types correctly implement the availability logic:
*   **AP Sensors** (`OpenEPaperLinkAPSensor` in `sensor.py`): The `available` property checks `self._hub.online`, and the entity listens to `f"{DOMAIN}_connection_status"` to update its state.
*   **AP Configuration Switches** (`APConfigSwitch` in `switch.py`): The `available` property checks `self._hub.online`, and the entity listens to `f"{DOMAIN}_connection_status"`.
*   **AP Configuration Selects** (`APConfigSelect` in `select.py`): The `available` property checks `self._hub.online`, and the entity listens to `f"{DOMAIN}_connection_status"`.
*   **AP Configuration Texts** (`APConfigText` in `text.py`): The `available` property checks `self._hub.online`, and the entity listens to `f"{DOMAIN}_connection_status"`.
*   **Camera Entities** (`EPDCamera` in `camera.py`): The `available` property checks `self._hub.online`, and the entity listens to `f"{DOMAIN}_connection_status"`.

However, the integration does not fully follow the rule for other entity types:

1.  **Tag Sensors (`OpenEPaperLinkTagSensor` in `sensor.py`):**
    *   The `available` property is `return self._tag_mac in self._hub.tags`. This only checks if the tag is known to the hub. It does **not** check if the hub (AP) itself is online (`self._hub.online`).
    *   The entity does **not** listen to the `f"{DOMAIN}_connection_status"` signal.
    *   As a result, if the AP goes offline, tag sensors will remain available (showing stale data) until the tag is eventually removed by `_verify_and_cleanup_tags` upon hub reconnection, or if another update happens to trigger `async_write_ha_state`. This is incorrect; they should become unavailable immediately when the AP (their data source via the hub) is offline.

2.  **Tag-Specific Buttons (`ClearPendingTagButton`, `ForceRefreshButton`, `RebootTagButton`, `ScanChannelsButton`, `DeepSleepButton` in `button.py`):**
    *   The `available` property for these buttons (e.g., `return self._tag_mac not in self._hub.get_blacklisted_tags()`) only checks if the tag is blacklisted. It does **not** check `self._hub.online`.
    *   These entities do **not** listen to `f"{DOMAIN}_connection_status"`.
    *   Since these buttons trigger actions that require communication with the AP (which in turn communicates with the tag), they should be unavailable if the AP is offline. Currently, they will appear available, and pressing them will result in a failed action (logged internally by `send_tag_cmd` but not reflected in entity availability).

3.  **AP Reboot Button (`RebootAPButton` in `button.py`):**
    *   This button lacks an explicit `available` property, meaning it defaults to `True`.
    *   It does **not** listen to `f"{DOMAIN}_connection_status"`.
    *   The action `reboot_ap` does check `hub.online`, but the button entity itself should reflect this unavailability in the UI.

4.  **Tag Name Text Input (`TagNameText` in `text.py`):**
    *   The `available` property (`return (self._hub.online and ...)`) correctly checks `self._hub.online`.
    *   However, it only listens to `f"{DOMAIN}_tag_update_{self._tag_mac}"` and not `f"{DOMAIN}_connection_status"`.
    *   If the hub goes offline and no specific tag update occurs, the entity's availability state in Home Assistant might not update promptly. It should listen to the connection status for better responsiveness.

## Suggestions

To make the `open_epaper_link` integration compliant with the `entity-unavailable` rule, the following changes are recommended:

1.  **For `OpenEPaperLinkTagSensor` (in `sensor.py`):**
    *   Modify the `available` property to include the hub's online status:
        ```python
        @property
        def available(self) -> bool:
            """Return if entity is available."""
            return self._hub.online and self._tag_mac in self._hub.tags
        ```
    *   In `async_added_to_hass`, add a dispatcher connection for `f"{DOMAIN}_connection_status"`:
        ```python
        async def async_added_to_hass(self) -> None:
            """Run when entity is added to register update signal handler."""
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    f"{DOMAIN}_tag_update_{self._tag_mac}",
                    self._handle_update,
                )
            )
            # Add this:
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    f"{DOMAIN}_connection_status",
                    self._handle_connection_status, # Assumes a new method like below
                )
            )

        @callback # Add this new method
        def _handle_connection_status(self, is_online: bool) -> None:
            """Handle connection status updates."""
            self.async_write_ha_state()
        ```

2.  **For Tag-Specific Buttons (`ClearPendingTagButton`, `ForceRefreshButton`, `RebootTagButton`, `ScanChannelsButton`, `DeepSleepButton` in `button.py`):**
    *   For each of these button classes, modify the `available` property. Example for `ClearPendingTagButton`:
        ```python
        @property
        def available(self) -> bool:
            """Return if entity is available."""
            # Add self._hub.online check
            return self._hub.online and self._tag_mac not in self._hub.get_blacklisted_tags()
        ```
    *   For each of these button classes, implement `async_added_to_hass` (if not present) or add to existing `async_added_to_hass` to listen for `f"{DOMAIN}_connection_status"` and update state. Create a common handler or individual handlers.
        ```python
        # Add to each relevant button class
        async def async_added_to_hass(self) -> None:
            """Register callbacks when entity is added to Home Assistant."""
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    f"{DOMAIN}_connection_status",
                    self._handle_connection_status,
                )
            )

        @callback
        def _handle_connection_status(self, is_online: bool) -> None:
            """Handle connection status updates."""
            self.async_write_ha_state()
        ```

3.  **For `RebootAPButton` (in `button.py`):**
    *   Add an `available` property:
        ```python
        @property
        def available(self) -> bool:
            """Return if entity is available."""
            return self._hub.online
        ```
    *   Implement `async_added_to_hass` to listen for `f"{DOMAIN}_connection_status"`:
        ```python
        async def async_added_to_hass(self) -> None:
            """Register callbacks when entity is added to Home Assistant."""
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    f"{DOMAIN}_connection_status",
                    self._handle_connection_status,
                )
            )

        @callback
        def _handle_connection_status(self, is_online: bool) -> None:
            """Handle connection status updates."""
            self.async_write_ha_state()
        ```

4.  **For `TagNameText` (in `text.py`):**
    *   Its `available` property is already correct.
    *   Enhance `async_added_to_hass` to also listen for `f"{DOMAIN}_connection_status"` for prompt UI updates:
        ```python
        async def async_added_to_hass(self):
            """Register callbacks when entity is added to Home Assistant."""
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    f"{DOMAIN}_tag_update_{self._tag_mac}",
                    self._handle_tag_update, # Existing handler for tag-specific data
                )
            )
            # Add this:
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    f"{DOMAIN}_connection_status",
                    self._handle_connection_status, # New handler for connection status
                )
            )

        @callback # Add this new method
        def _handle_connection_status(self, is_online: bool) -> None:
            """Handle connection status updates."""
            # This will re-evaluate the existing 'available' property
            self.async_write_ha_state()
        ```

By implementing these changes, all entities in the `open_epaper_link` integration will correctly reflect their availability based on the AP's connection status, thus adhering to the `entity-unavailable` rule.

_Created at 2025-05-14 20:49:47. Prompt tokens: 60731, Output tokens: 2409, Total tokens: 69095_
