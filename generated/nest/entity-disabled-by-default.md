# nest: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default)                                                     |
| Status | **todo**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `entity-disabled-by-default` rule requires that integrations disable less popular or noisy entities by default. This is to conserve system resources by not tracking the history of entities that change state frequently (noisy) or are not useful to most users (less popular), unless a user explicitly enables them.

The `nest` integration creates several types of entities:
*   **Climate entities** (from `climate.py`): These represent thermostats and their core functions (temperature, humidity, HVAC mode, presets, fan mode). These are primary functionalities and are not typically "less popular" or excessively "noisy." Their current default-enabled status is appropriate.
*   **Camera entities** (from `camera.py`): These provide video streams from Nest cameras. This is a primary function and being enabled by default is appropriate.
*   **Sensor entities** (from `sensor.py`): Specifically, `TemperatureSensor` and `HumiditySensor` derived from thermostat traits. These represent core environmental data and are neither "less popular" nor inherently "noisy." Their current default-enabled status is appropriate.
*   **Event entities** (from `event.py`): These entities represent discrete events from devices.
    *   The `event` entity for doorbell chimes (created from `NestEventEntityDescription` with `key=EVENT_DOORBELL_CHIME`) represents a primary function and is not typically excessively noisy. Its current default-enabled status is appropriate.
    *   However, the `event` entity that represents camera motion, person, and sound detection (created from `NestEventEntityDescription` with `key=EVENT_CAMERA_MOTION`, translation key "motion") aggregates multiple underlying event types (Nest API events: `CAMERA_MOTION`, `CAMERA_PERSON`, `CAMERA_SOUND`). The state of this Home Assistant `EventEntity` is the timestamp of the last detected event of *any* of these types.

The issue lies with this combined camera event entity (`event.motion`):
1.  **Potential for Noisiness:** If a camera is placed in an environment with frequent general motion (e.g., facing a busy area, trees moving in wind) or frequent sounds, this entity's state will update very often. This qualifies it as "noisy" according to the rule, as frequent state changes lead to increased database writes and system load for history tracking.
2.  **Rule Application:** The rule states that entities which are "less popular OR noisy" should be disabled by default. Even if person detection (one component of this bundled entity) is popular, the entity as a whole can be noisy due to other components like general motion or sound.
3.  **Current Implementation:** This combined camera event entity (`event.motion`) is currently enabled by default, as its `NestEventEntityDescription` in `homeassistant/components/nest/event.py` does not set `entity_registry_enabled_default=False`.

Therefore, the `nest` integration does not fully follow the `entity-disabled-by-default` rule because the potentially noisy combined camera event entity is enabled by default.

## Suggestions

To make the `nest` integration compliant with the `entity-disabled-by-default` rule, the combined camera event entity (motion, person, sound) should be disabled by default.

1.  **Modify `NestEventEntityDescription`:**
    In `homeassistant/components/nest/event.py`, locate the `ENTITY_DESCRIPTIONS` list. For the `NestEventEntityDescription` corresponding to camera motion/person/sound events (identified by `key=EVENT_CAMERA_MOTION`), add the property `entity_registry_enabled_default=False`.

    **Current Code (in `homeassistant/components/nest/event.py`):**
    ```python
    ENTITY_DESCRIPTIONS = [
        # ... other descriptions ...
        NestEventEntityDescription(
            key=EVENT_CAMERA_MOTION,
            translation_key="motion",
            device_class=EventDeviceClass.MOTION,
            event_types=[EVENT_CAMERA_MOTION, EVENT_CAMERA_PERSON, EVENT_CAMERA_SOUND],
            trait_types=[
                TraitType.CAMERA_MOTION,
                TraitType.CAMERA_PERSON,
                TraitType.CAMERA_SOUND,
            ],
            api_event_types=[
                EventType.CAMERA_MOTION,
                EventType.CAMERA_PERSON,
                EventType.CAMERA_SOUND,
            ],
        ),
    ]
    ```

    **Suggested Change:**
    ```python
    ENTITY_DESCRIPTIONS = [
        # ... other descriptions ...
        NestEventEntityDescription(
            key=EVENT_CAMERA_MOTION,
            translation_key="motion",
            device_class=EventDeviceClass.MOTION,
            event_types=[EVENT_CAMERA_MOTION, EVENT_CAMERA_PERSON, EVENT_CAMERA_SOUND],
            trait_types=[
                TraitType.CAMERA_MOTION,
                TraitType.CAMERA_PERSON,
                TraitType.CAMERA_SOUND,
            ],
            api_event_types=[
                EventType.CAMERA_MOTION,
                EventType.CAMERA_PERSON,
                EventType.CAMERA_SOUND,
            ],
            entity_registry_enabled_default=False,  # <--- ADD THIS LINE
        ),
    ]
    ```

2.  **Reasoning for Suggestion:**
    *   **Compliance:** This change makes the potentially "noisy" entity disabled by default, adhering to the rule's requirement.
    *   **Resource Conservation:** It prevents frequent state updates and history logging for this entity unless the user explicitly enables it, reducing database size and I/O.
    *   **User Choice:** Users who specifically need this combined event entity (including person, general motion, and sound events) can easily enable it from the entity registry. This ensures that users who value this information can still access it, while users who find it too noisy or don't need all aggregated events are not burdened by default.

By implementing this change, the `nest` integration will better align with the best practices for entity management and resource usage in Home Assistant.

_Created at 2025-05-28 23:09:58. Prompt tokens: 32407, Output tokens: 1453, Total tokens: 39833_
