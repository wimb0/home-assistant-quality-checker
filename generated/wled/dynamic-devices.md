# wled: dynamic-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [dynamic-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `dynamic-devices` rule mandates that an integration should automatically create relevant entities for new devices (or sub-devices) that appear after the initial integration setup.

This rule applies to the `wled` integration because a WLED device can be configured with multiple segments. These segments can be added, removed, or reconfigured by the user on the WLED device itself, even after the WLED integration has been set up in Home Assistant. Entities associated with these segments (e.g., lights, numbers, selects, switches) should therefore be dynamically added to Home Assistant as new segments become available.

The `wled` integration correctly follows this rule. It implements a mechanism to detect new WLED segments and dynamically creates the corresponding entities. This is primarily handled by an `async_update_segments` function pattern found in several platform files:

*   **`light.py`**:
    *   The `async_setup_entry` function initializes a `current_ids` set to track known segment IDs and calls `async_update_segments`.
    *   The `async_update_segments` function (lines 151-170) is registered as a listener to the `WLEDDataUpdateCoordinator`.
    *   On each update, this function retrieves the current `segment_ids` from `coordinator.data.state.segments`.
    *   It then compares `segment_ids` with `current_ids` to find new segments (`segment_ids - current_ids`).
    *   For each new segment, a `WLEDSegmentLight` entity is created and added using `async_add_entities`.
    *   The `current_ids` set is updated with the newly added segment ID.
    *   This file also dynamically adds/removes a `WLEDMainLight` entity based on the number of segments and the `keep_main_light` option, further demonstrating dynamic entity management.

*   **`number.py`**:
    *   This platform follows an identical pattern to `light.py`. The `async_update_segments` function (lines 74-91) dynamically adds `WLEDNumber` entities (for speed and intensity) for new segments.

*   **`select.py`**:
    *   Similarly, the `async_update_segments` function (lines 148-163) dynamically adds `WLEDPaletteSelect` entities for new segments. Other select entities (`WLEDLiveOverrideSelect`, `WLEDPresetSelect`, `WLEDPlaylistSelect`) are device-global and are not segment-specific, so they are added once.

*   **`switch.py`**:
    *   This platform also uses the `async_update_segments` function (lines 136-151) to dynamically add `WLEDReverseSwitch` entities for new segments. Other switch entities (`WLEDNightlightSwitch`, `WLEDSyncSendSwitch`, `WLEDSyncReceiveSwitch`) are device-global.

This implementation aligns perfectly with the example provided in the `dynamic-devices` rule documentation, where a coordinator provides data, and a listener function checks for new devices/sub-devices and adds entities accordingly.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 22:59:34. Prompt tokens: 21933, Output tokens: 810, Total tokens: 24973_
