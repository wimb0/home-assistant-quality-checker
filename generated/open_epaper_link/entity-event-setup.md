# open_epaper_link: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-event-setup` rule requires that entities subscribing to events (e.g., from the integration's hub or coordinator) do so in `async_added_to_hass` and unsubscribe correctly, typically by registering the unsubscribe callback with `self.async_on_remove()`. This ensures that entities update their state correctly when events occur and that resources are cleaned up when entities are removed.

This rule applies to the `open_epaper_link` integration because its entities (sensors, cameras, switches, selects, text inputs, buttons) receive updates from the central `Hub` class via `async_dispatcher_connect`. This mechanism is a form of event subscription.

Several entity types in the `open_epaper_link` integration correctly follow this rule:
*   **Sensor Entities (`sensor.py`):** Both `OpenEPaperLinkTagSensor` and `OpenEPaperLinkAPSensor` use `self.async_on_remove(async_dispatcher_connect(...))` within their `async_added_to_hass` methods to subscribe to relevant updates (e.g., tag data, AP status, connection status) and ensure proper cleanup.
*   **Camera Entities (`camera.py`):** `EPDCamera` correctly subscribes to tag image updates and connection status changes in `async_added_to_hass` using `self.async_on_remove()`.
*   **Select Entities (`select.py`):** `APConfigSelect` (and by extension `APTimeHourSelect`) subscribes to AP configuration updates and connection status changes in `async_added_to_hass` using `self.async_on_remove()`.
*   **Switch Entities (`switch.py`):** `APConfigSwitch` subscribes to AP configuration updates and connection status changes in `async_added_to_hass` using `self.async_on_remove()`.
*   **AP Text Entities (`text.py`):** `APConfigText` subscribes to AP configuration updates and connection status changes in `async_added_to_hass` using `self.async_on_remove()`.

However, some entity types do not fully adhere to this rule, primarily concerning the update of their `available` state in response to hub or tag status changes:

1.  **Tag-specific Button Entities (`button.py`):**
    Classes like `ClearPendingTagButton`, `ForceRefreshButton`, `RebootTagButton`, `ScanChannelsButton`, and `DeepSleepButton`.
    *   Their `available` property is currently defined as:
        ```python
        # button.py (e.g., ClearPendingTagButton)
        @property
        def available(self) -> bool:
            return self._tag_mac not in self._hub.get_blacklisted_tags()
        ```
    *   While the `async_setup_entry` in `button.py` handles the *removal* of entities if a tag is blacklisted, and the hub handles removal if a tag is deleted from the AP, the `available` property of an existing button does not react to the hub's online/offline status. If the hub is offline, these buttons should be unavailable as commands cannot be sent.
    *   They are missing subscriptions to `f"{DOMAIN}_connection_status"` to update their availability based on `self._hub.online`. Their `available` property should also check `self._hub.online` and ideally `self._tag_mac in self._hub.tags`.

2.  **AP-specific Button Entity (`button.py`):**
    The `RebootAPButton` class.
    *   It currently lacks an `available` property, meaning it defaults to being always available.
    *   Its availability should depend on `self._hub.online`.
    *   It is missing a subscription to `f"{DOMAIN}_connection_status"` in `async_added_to_hass`.

3.  **Tag Name Text Entity (`text.py`):**
    The `TagNameText` class.
    *   Its `available` property is defined as:
        ```python
        # text.py (TagNameText)
        @property
        def available(self) -> bool:
            return (
                    self._hub.online and
                    self._tag_mac in self._hub.tags and # Covered by existing _tag_update_ subscription
                    self._tag_mac not in self._hub.get_blacklisted_tags()
            )
        ```
    *   It correctly subscribes to `f"{DOMAIN}_tag_update_{self._tag_mac}"` which handles changes to `self._tag_mac in self._hub.tags`.
    *   However, it is missing subscriptions to:
        *   `f"{DOMAIN}_connection_status"` to react to changes in `self._hub.online`.
        *   `f"{DOMAIN}_blacklist_update"` to react to changes in `self._hub.get_blacklisted_tags()`. Unlike buttons, the `async_setup_entry` for `text.py` does not remove `TagNameText` entities if a tag is blacklisted post-creation; it only prevents initial creation. Thus, the entity itself needs to manage its availability based on blacklist changes.

Because these entities do not subscribe to all relevant events to update their state (specifically their `available` attribute), the integration is not fully compliant with the `entity-event-setup` rule.

## Suggestions

To make the `open_epaper_link` integration compliant with the `entity-event-setup` rule, the following changes are recommended:

**1. For Tag-specific Button Entities in `button.py` (e.g., `ClearPendingTagButton`, `ForceRefreshButton`, etc.):**

*   Update the `available` property to include checks for hub online status and tag existence:
    ```python
    # In classes like ClearPendingTagButton
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self._hub.online and
            self._tag_mac in self._hub.tags and # Ensure tag is still known by hub
            self._tag_mac not in self._hub.get_blacklisted_tags()
        )
    ```
*   Implement `async_added_to_hass` to subscribe to necessary signals:
    ```python
    # In classes like ClearPendingTagButton
    async def async_added_to_hass(self) -> None:
        """Run when entity is added to register update signal handlers."""
        await super().async_added_to_hass() # If inheriting from a class that has it
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_connection_status",
                self._handle_connection_status_update,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_tag_update_{self._tag_mac}", # For self._tag_mac in self._hub.tags
                self._handle_tag_or_blacklist_update,
            )
        )
        # The existing async_setup_entry mechanism for blacklist updates removes entities.
        # If an entity is not removed but should become unavailable due to blacklisting,
        # it would also need to listen to DOMAIN_blacklist_update.
        # Given the current setup, hub.online and hub.tags are the main missing checks for availability.
        # For simplicity, one callback can handle multiple reasons for state write.
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_blacklist_update",
                self._handle_tag_or_blacklist_update, # For blacklist check
            )
        )


    @callback
    def _handle_connection_status_update(self, is_online: bool) -> None:
        """Handle hub connection status updates."""
        self.async_write_ha_state()

    @callback
    def _handle_tag_or_blacklist_update(self) -> None: # Or pass data if needed
        """Handle tag data or blacklist updates."""
        self.async_write_ha_state()
    ```

**2. For `RebootAPButton` in `button.py`:**

*   Add an `available` property:
    ```python
    # In RebootAPButton class
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._hub.online
    ```
*   Implement `async_added_to_hass` to subscribe to connection status:
    ```python
    # In RebootAPButton class
    async def async_added_to_hass(self) -> None:
        """Run when entity is added to register update signal handler."""
        await super().async_added_to_hass() # If inheriting
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_connection_status",
                self._handle_connection_status_update,
            )
        )

    @callback
    def _handle_connection_status_update(self, is_online: bool) -> None:
        """Handle hub connection status updates."""
        self.async_write_ha_state()
    ```

**3. For `TagNameText` in `text.py`:**

*   The `available` property already checks `self._hub.online` and blacklist status.
*   Modify `async_added_to_hass` to include subscriptions for connection status and blacklist updates:
    ```python
    # In TagNameText class
    async def async_added_to_hass(self):
        """Register callbacks when entity is added to Home Assistant."""
        # Existing subscription
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_tag_update_{self._tag_mac}",
                self._handle_tag_update, # Existing callback
            )
        )
        # Add subscription for connection status
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_connection_status",
                self._handle_status_update, # Generic handler or specific one
            )
        )
        # Add subscription for blacklist update
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_blacklist_update",
                self._handle_status_update, # Generic handler or specific one
            )
        )

    @callback
    def _handle_tag_update(self): # Keep existing specific handler
        """Handle tag updates."""
        self.async_write_ha_state()

    @callback
    def _handle_status_update(self, *args) -> None: # Generic handler for other updates
        """Handle connection or blacklist status updates."""
        # The *args is to accommodate different dispatcher payloads if any.
        # If no payload, it's not needed.
        self.async_write_ha_state()
    ```

By implementing these changes, the entities will correctly subscribe to all relevant events impacting their state (including availability) within `async_added_to_hass` and use `self.async_on_remove` for cleanup, thus fully complying with the `entity-event-setup` rule. This ensures their `available` status is promptly and accurately updated.

_Created at 2025-05-14 20:36:37. Prompt tokens: 60657, Output tokens: 2704, Total tokens: 69369_
