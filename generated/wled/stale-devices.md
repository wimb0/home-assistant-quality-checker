# wled: stale-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [stale-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/stale-devices)                                                     |
| Status | **todo**                                                                 |

## Overview

The `stale-devices` rule mandates that when a device (or a significant sub-component behaving like a device) is removed from its source (e.g., a hub or account), it should also be removed from Home Assistant to prevent the UI from showing unavailable items. The WLED integration manages a primary WLED controller as a Home Assistant device, and also dynamically creates entities for "segments" configured on that WLED controller. These segments can be added or removed by the user on the WLED device itself.

The rule applies to the WLED integration, particularly concerning its handling of these dynamic segment-based entities. While the primary WLED device is correctly removed from Home Assistant when its config entry is deleted, the entities representing WLED segments are not removed if the corresponding segments are deleted from the WLED controller.

Currently, the WLED integration correctly adds entities for newly discovered segments. For example, in `light.py`, the `async_update_segments` function identifies new segments and adds `WLEDSegmentLight` entities for them. Similar logic exists in `number.py` for speed/intensity numbers, `select.py` for color palette selectors, and `switch.py` for reverse switches, all based on segments.

However, none of these `async_update_segments` functions implement logic to remove entities when their corresponding segments are no longer reported by the WLED device.
For instance, the `async_update_segments` function in `light.py` (and similarly in other files like `number.py`, `select.py`, `switch.py`):
```python
# light.py
@callback
def async_update_segments(
    coordinator: WLEDDataUpdateCoordinator,
    current_ids: set[int], # Tracks segment IDs for which entities have been created
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    # ...
    segment_ids = { # Segments currently on the WLED device
        light.segment_id
        for light in coordinator.data.state.segments.values()
        # ...
    }
    # ...
    # Process new segments, add them to Home Assistant
    for segment_id in segment_ids - current_ids: # Only processes (device_segments - ha_known_segments)
        current_ids.add(segment_id)
        new_entities.append(WLEDSegmentLight(coordinator, segment_id))
    # ...
    async_add_entities(new_entities)
```
This code only adds new entities (`segment_ids - current_ids`) but does not handle `current_ids - segment_ids` (segments known to HA but no longer on the device). As a result, if a user deletes a segment on their WLED device, the corresponding Home Assistant entities will persist, likely becoming "unavailable," instead of being removed from the system. This does not meet the rule's requirement to remove stale items.

The integration does not need to implement `async_remove_config_entry_device` for the main WLED device, as the removal of the WLED device itself is appropriately tied to the deletion of its config entry. The issue lies specifically with the lifecycle management of segment-based entities.

## Suggestions

To comply with the `stale-devices` rule, the WLED integration needs to modify the `async_update_segments` callback function in each relevant platform file (`light.py`, `number.py`, `select.py`, and `switch.py`) to handle the removal of entities for segments that no longer exist.

The general approach for each platform's `async_update_segments` function should be:

1.  **Get Hass and Entity Registry**: Obtain the `hass` object from the coordinator and get an instance of the `EntityRegistry`.
    ```python
    from homeassistant.helpers import entity_registry as er
    # ...
    hass = coordinator.hass
    entity_registry = er.async_get(hass)
    ```
2.  **Identify Active Segments**: Get the set of current segment IDs from `coordinator.data.state.segments`.
3.  **Identify Stale Segments**: Compare the set of segment IDs for which entities currently exist in Home Assistant (tracked by the `current_ids` set passed to the function) with the set of active segment IDs from the device. The difference (`current_ids - active_segment_ids_from_device`) represents stale segments.
4.  **Remove Stale Entities**: For each stale segment ID:
    *   Construct the `unique_id` for each type of entity associated with that segment (e.g., light, speed number, intensity number, palette select, reverse switch).
    *   Use `entity_registry.async_get_entity_id(PLATFORM_DOMAIN, DOMAIN, unique_id)` to find the `entity_id`.
    *   If the `entity_id` exists, call `entity_registry.async_remove_entity(entity_id)`.
5.  **Update Tracked IDs**: Remove the stale segment IDs from the `current_ids` set.
6.  **Add New Entities**: Proceed with the existing logic to add entities for new segments (`active_segment_ids_from_device - current_ids`).

**Example modification for `light.py`'s `async_update_segments`:**

```python
# In light.py
from homeassistant.helpers import entity_registry as er
from homeassistant.const import Platform # Add Platform import
# ... other imports ...
# from .const import DOMAIN, LOGGER (if logging)

@callback
def async_update_segments(
    coordinator: WLEDDataUpdateCoordinator,
    current_light_segment_ids: set[int], # Consider renaming for clarity per platform
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Update light segments, adding new ones and removing stale ones."""
    hass = coordinator.hass
    entity_registry = er.async_get(hass)

    active_segment_ids_from_device = {
        segment.segment_id
        for segment in coordinator.data.state.segments.values()
        if segment.segment_id is not None
    }

    # Identify and remove stale light entities
    stale_segment_ids = current_light_segment_ids - active_segment_ids_from_device
    for segment_id in stale_segment_ids:
        # Construct unique_id for the WLEDSegmentLight entity
        # This matches WLEDSegmentLight._attr_unique_id format
        unique_id = f"{coordinator.data.info.mac_address}_{segment_id}"
        if entity_id := entity_registry.async_get_entity_id(
            Platform.LIGHT, DOMAIN, unique_id
        ):
            entity_registry.async_remove_entity(entity_id)
            # LOGGER.debug("Removed stale WLED segment light entity for segment %s", segment_id)
    current_light_segment_ids.difference_update(stale_segment_ids) # Update the set

    # Add new light entities (WLEDMainLight logic should be preserved if separate)
    new_light_entities: list[WLEDSegmentLight] = []
    # Ensure main light logic is handled correctly if it's part of this callback in the original code

    for segment_id in active_segment_ids_from_device - current_light_segment_ids:
        new_light_entities.append(WLEDSegmentLight(coordinator, segment_id))
        current_light_segment_ids.add(segment_id) # Add to tracked set

    if new_light_entities:
        async_add_entities(new_light_entities)

    # Note: Original code for adding WLEDMainLight might need to be adjusted
    # if it's within the same async_update_segments callback and relies on 'current_ids'.
    # The example above focuses on WLEDSegmentLight.
```

**Modifications for other platforms (e.g., `number.py`):**
The `async_update_segments` in `number.py` creates multiple entities (speed and intensity) per segment based on `NUMBERS` (a list of `WLEDNumberEntityDescription`). The removal logic must iterate through these descriptions to construct the correct unique IDs for removal.

```python
# Conceptual change for number.py's async_update_segments
# from .const import DOMAIN, LOGGER (if logging)
# from homeassistant.const import Platform # Add Platform import
# from .sensor import NUMBERS (assuming NUMBERS is defined with description keys)

@callback
def async_update_segments(
    coordinator: WLEDDataUpdateCoordinator,
    current_number_segment_ids: set[int], # Tracks segments for which number entities exist
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Update number entities for segments."""
    hass = coordinator.hass
    entity_registry = er.async_get(hass)

    active_segment_ids_from_device = {
        segment.segment_id
        for segment in coordinator.data.state.segments.values()
        if segment.segment_id is not None
    }

    # Remove stale number entities
    stale_segment_ids = current_number_segment_ids - active_segment_ids_from_device
    for segment_id in stale_segment_ids:
        for description in NUMBERS: # For both speed and intensity descriptions
            # Matches WLEDNumber._attr_unique_id format
            unique_id = f"{coordinator.data.info.mac_address}_{description.key}_{segment_id}"
            if entity_id := entity_registry.async_get_entity_id(
                Platform.NUMBER, DOMAIN, unique_id
            ):
                entity_registry.async_remove_entity(entity_id)
                # LOGGER.debug("Removed stale WLED number entity (%s) for segment %s", description.key, segment_id)
    current_number_segment_ids.difference_update(stale_segment_ids)

    # Add new number entities
    new_number_entities: list[WLEDNumber] = []
    for segment_id in active_segment_ids_from_device - current_number_segment_ids:
        new_number_entities.extend(
            WLEDNumber(coordinator, segment_id, desc) for desc in NUMBERS
        )
        current_number_segment_ids.add(segment_id)

    if new_number_entities:
        async_add_entities(new_number_entities)
```

This same pattern of identifying stale segments and removing their associated entities via the `EntityRegistry` should be applied to:
*   `select.py` for `WLEDPaletteSelect` entities.
*   `switch.py` for `WLEDReverseSwitch` entities.

Each platform's `async_update_segments` function is responsible for managing the lifecycle of its specific segment-based entities. The `current_ids` set captured by `functools.partial` for each platform is distinct and will correctly track the entities managed by that platform. Ensure that the `unique_id` construction in the removal logic exactly matches how unique IDs are defined in the entity classes.

_Created at 2025-05-10 23:08:33. Prompt tokens: 22998, Output tokens: 2634, Total tokens: 34114_
