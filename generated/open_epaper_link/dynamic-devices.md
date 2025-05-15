# open_epaper_link: dynamic-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [dynamic-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices)                                                     |
| Status | **done**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `dynamic-devices` rule requires that an integration automatically creates relevant entities for new devices that are connected or discovered after the initial setup of the integration. This ensures a good user experience, as users do not need to manually reconfigure or reload the integration to see newly added hardware.

This rule applies to the `open_epaper_link` integration because it acts as a hub for E-Paper Tags (ESL tags). These tags are the "devices" in the context of this rule, and new tags can be added to the OpenEPaperLink Access Point (AP) at any time after the Home Assistant integration has been set up.

The `open_epaper_link` integration **fully follows** this rule.

The mechanism for handling newly discovered tags is implemented as follows:

1.  **Device Discovery in the Hub:**
    The `Hub` class (in `homeassistant/components/open_epaper_link/hub.py`) is responsible for communication with the OpenEPaperLink AP and managing tag data.
    *   The `_process_tag_data` method in `hub.py` is called when new data for a tag is received (e.g., via WebSocket message in `_handle_tag_message` or during initial load in `async_load_all_tags`).
    *   This method checks if the tag is new by comparing its MAC address against a set of `_known_tags`:
        ```python
        # hub.py
        is_new_tag = tag_mac not in self._known_tags
        # ...
        if is_new_tag:
            self._known_tags.add(tag_mac)
            _LOGGER.debug("Discovered new tag: %s", tag_mac)
            # Fire discovery event before saving
            async_dispatcher_send(self.hass, f"{DOMAIN}_tag_discovered", tag_mac)
        ```
    *   If `is_new_tag` is true, the tag's MAC address is added to `_known_tags`, and a signal `f"{DOMAIN}_tag_discovered"` is dispatched using `async_dispatcher_send`, with the new tag's MAC address as an argument.

2.  **Entity Platform Handling of New Devices:**
    The entity platforms that create entities for individual tags (e.g., `sensor.py`, `camera.py`, `button.py`, `text.py`) listen for this `_tag_discovered` signal.
    *   In the `async_setup_entry` function of these platform files, a callback function is defined (e.g., `async_add_tag_sensor` in `sensor.py`).
    *   This callback function is responsible for creating all relevant entities for the newly discovered tag and adding them to Home Assistant using the `async_add_entities` callback.
    *   The callback is registered as a listener for the `_tag_discovered` signal using `async_dispatcher_connect`. For example, in `sensor.py`:
        ```python
        # sensor.py
        @callback
        def async_add_tag_sensor(tag_mac: str) -> None:
            entities = []
            for description in TAG_SENSOR_TYPES:
                sensor = OpenEPaperLinkTagSensor(hub, tag_mac, description)
                entities.append(sensor)
            async_add_entities(entities)

        # Register callback for new tag discovery
        entry.async_on_unload(
            async_dispatcher_connect(
                hass,
                f"{DOMAIN}_tag_discovered",
                async_add_tag_sensor
            )
        )
        ```
    *   This pattern is consistently used across:
        *   `sensor.py` for `OpenEPaperLinkTagSensor` entities.
        *   `camera.py` for `EPDCamera` entities.
        *   `button.py` for various tag-specific button entities (e.g., `ClearPendingTagButton`, `ForceRefreshButton`).
        *   `text.py` for `TagNameText` entities.

Platforms like `switch.py` and `select.py` only create entities related to the AP itself, not for individual tags. Therefore, they do not need to subscribe to the `_tag_discovered` signal for adding tag-specific entities, as no such entities are defined for them. This is compliant with the rule, as only "relevant entities for the device" (the tag) need to be created.

This implementation ensures that when a new E-Paper Tag is recognized by the AP and its information is relayed to Home Assistant, all associated entities (sensors, camera, buttons, text input for alias) are automatically created and made available without requiring user intervention.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 20:59:02. Prompt tokens: 60629, Output tokens: 1182, Total tokens: 64881_
