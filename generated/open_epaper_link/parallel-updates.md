# open_epaper_link: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates)                                                     |
| Status | **todo**                                                                 |

## Overview

The `parallel-updates` rule applies to this integration because it provides entities via multiple platforms: `sensor`, `button`, `camera`, `select`, `switch`, and `text`. The rule mandates that the `PARALLEL_UPDATES` constant should be explicitly defined in each entity platform file to control the concurrency of updates and action calls to the device or service.

The `open_epaper_link` integration currently does **not** follow this rule. None of its entity platform files define the `PARALLEL_UPDATES` constant:
*   `homeassistant/components/open_epaper_link/sensor.py`
*   `homeassistant/components/open_epaper_link/button.py`
*   `homeassistant/components/open_epaper_link/camera.py`
*   `homeassistant/components/open_epaper_link/select.py`
*   `homeassistant/components/open_epaper_link/switch.py`
*   `homeassistant/components/open_epaper_link/text.py`

Without `PARALLEL_UPDATES` being explicitly set, Home Assistant's default behavior for parallel operations will apply, which might not be optimal for the OpenEPaperLink AP (an ESP32-based device that could be sensitive to concurrent requests).

## Suggestions

To make the `open_epaper_link` integration compliant with the `parallel-updates` rule, the `PARALLEL_UPDATES` constant should be added at the module level in each of its entity platform files.

1.  **For read-only platforms using the Hub for data updates:**
    The `Hub` class (`hub.py`) centralizes data fetching and updates via a WebSocket connection and dispatches updates to entities. This is analogous to the data coordinator pattern mentioned in the rule. For such read-only platforms, `PARALLEL_UPDATES = 0` is appropriate, as the data updates are already centralized.

    *   In `homeassistant/components/open_epaper_link/sensor.py`, add:
        ```python
        PARALLEL_UPDATES = 0
        ```
        **Reasoning:** Sensor entities are read-only and receive updates dispatched by the central `Hub`. `PARALLEL_UPDATES = 0` indicates that Home Assistant does not need to manage parallel polling for these entities.

    *   In `homeassistant/components/open_epaper_link/camera.py`, add:
        ```python
        PARALLEL_UPDATES = 0
        ```
        **Reasoning:** Camera entities primarily fetch images. While `async_camera_image` can make HTTP requests, the entity state updates are often tied to dispatches from the `Hub`. Setting to `0` aligns with the coordinator pattern for updates. The actual image fetching is on-demand.

2.  **For platforms performing actions (sending commands/requests to the AP):**
    Entities on these platforms make direct HTTP requests to the OpenEPaperLink AP when an action is triggered (e.g., pressing a button, toggling a switch). To prevent overwhelming the AP, especially if multiple actions are triggered simultaneously (e.g., by an automation), limiting concurrency is advisable. `PARALLEL_UPDATES = 1` is a common safe default, ensuring actions are processed sequentially for that platform.

    *   In `homeassistant/components/open_epaper_link/button.py`, add:
        ```python
        PARALLEL_UPDATES = 1
        ```
        **Reasoning:** Button entities trigger commands (e.g., `send_tag_cmd`, `reboot_ap`) which involve HTTP requests to the AP. `PARALLEL_UPDATES = 1` will ensure that if multiple `open_epaper_link` buttons are pressed concurrently, their `async_press` methods are executed one at a time for this platform.

    *   In `homeassistant/components/open_epaper_link/select.py`, add:
        ```python
        PARALLEL_UPDATES = 1
        ```
        **Reasoning:** Select entities change AP configuration via `set_ap_config_item`, which makes an HTTP POST request. Limiting to one concurrent action helps protect the AP.

    *   In `homeassistant/components/open_epaper_link/switch.py`, add:
        ```python
        PARALLEL_UPDATES = 1
        ```
        **Reasoning:** Switch entities change AP configuration via `set_ap_config_item`. Similar to select entities, `PARALLEL_UPDATES = 1` is a good default.

    *   In `homeassistant/components/open_epaper_link/text.py`, add:
        ```python
        PARALLEL_UPDATES = 1
        ```
        **Reasoning:** Text entities can update AP configuration (`APConfigText` via `set_ap_config_item`) or tag aliases (`TagNameText` via direct HTTP POST). `PARALLEL_UPDATES = 1` will serialize these actions for this platform.

By implementing these changes, the integration will explicitly define its concurrency behavior for entity updates and actions, adhering to the `parallel-updates` rule and potentially improving stability when interacting with the OpenEPaperLink AP.

_Created at 2025-05-14 20:52:35. Prompt tokens: 60449, Output tokens: 1280, Total tokens: 64455_
