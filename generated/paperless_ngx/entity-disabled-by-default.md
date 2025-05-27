# paperless_ngx: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [paperless_ngx](https://www.home-assistant.io/integrations/paperless_ngx/) |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-disabled-by-default` rule requires that integrations disable less popular or noisy entities by default. This helps conserve resources and reduce UI clutter for users who may not need these specific entities, while still allowing interested users to enable them manually.

This rule applies to the `paperless_ngx` integration because it creates several sensor entities that report various statistics from a Paperless-ngx instance. The provided entities are:
*   `sensor.documents_total`
*   `sensor.documents_inbox`
*   `sensor.characters_count`
*   `sensor.tag_count`
*   `sensor.correspondent_count`
*   `sensor.document_type_count`

While `documents_total` and `documents_inbox` can be considered primary and essential statistics for most users, other entities like `characters_count`, and potentially `tag_count`, `correspondent_count`, and `document_type_count`, might be considered "less popular". For example, the total character count across all documents (`characters_count`) is a very granular statistic that might not be of interest to every user. Similarly, counts of metadata items (tags, correspondents, document types) might be secondary for users primarily focused on document flow.

The integration currently does **not** follow this rule.
All sensor entities are enabled by default. This is determined by examining `homeassistant/components/paperless_ngx/sensor.py`:
1.  The `PaperlessEntityDescription` dataclass inherits from `SensorEntityDescription`.
2.  The `SensorEntityDescription` class in Home Assistant Core (from which `PaperlessEntityDescription` inherits) has a field `entity_registry_enabled_default: bool = True`.
3.  The instances of `PaperlessEntityDescription` defined in the `SENSOR_DESCRIPTIONS` tuple in `homeassistant/components/paperless_ngx/sensor.py` do not override this default for any of the sensor types. For example:
    ```python
    # homeassistant/components/paperless_ngx/sensor.py
    SENSOR_DESCRIPTIONS: tuple[PaperlessEntityDescription, ...] = (
        PaperlessEntityDescription(
            key="documents_total",
            translation_key="documents_total",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.documents_total,
            # No entity_registry_enabled_default=False here
        ),
        PaperlessEntityDescription(
            key="characters_count",
            translation_key="characters_count",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.character_count,
            # No entity_registry_enabled_default=False here
        ),
        # ... and so on for other entities
    )
    ```
As a result, all entities provided by this integration are enabled by default, including those that could be argued are "less popular."

## Suggestions

To comply with the `entity-disabled-by-default` rule, the integration should identify entities that are likely to be less popular or potentially noisy and disable them by default. Users who need these entities can then enable them manually through the Home Assistant UI.

1.  **Identify Less Popular Entities:**
    Review the list of provided sensor entities:
    *   `sensor.documents_total` (Likely popular, keep enabled)
    *   `sensor.documents_inbox` (Likely popular and actionable, keep enabled)
    *   `sensor.characters_count` (Strong candidate for being disabled by default due to its granular nature)
    *   `sensor.tag_count` (Candidate for being disabled by default)
    *   `sensor.correspondent_count` (Candidate for being disabled by default)
    *   `sensor.document_type_count` (Candidate for being disabled by default)

    The entity `characters_count` is a prime candidate for being disabled by default. Consideration should also be given to `tag_count`, `correspondent_count`, and `document_type_count`, as these metadata counts might not be essential for all users.

2.  **Update Entity Descriptions:**
    For each entity identified as "less popular," add `entity_registry_enabled_default=False` to its `PaperlessEntityDescription` in the `SENSOR_DESCRIPTIONS` tuple located in `homeassistant/components/paperless_ngx/sensor.py`.

    **Example for `characters_count`:**
    Modify the definition in `homeassistant/components/paperless_ngx/sensor.py` as follows:

    ```python
    # homeassistant/components/paperless_ngx/sensor.py

    # ... (other imports and code) ...

    SENSOR_DESCRIPTIONS: tuple[PaperlessEntityDescription, ...] = (
        PaperlessEntityDescription(
            key="documents_total",
            translation_key="documents_total",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.documents_total,
            # This entity is popular, so it remains enabled by default (or explicitly True)
            # entity_registry_enabled_default=True, # Default is True, so explicit set not strictly needed
        ),
        PaperlessEntityDescription(
            key="documents_inbox",
            translation_key="documents_inbox",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.documents_inbox,
            # This entity is popular, so it remains enabled by default
        ),
        PaperlessEntityDescription(
            key="characters_count",
            translation_key="characters_count",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.character_count,
            entity_registry_enabled_default=False,  # <--- Add this line
        ),
        PaperlessEntityDescription(
            key="tag_count",
            translation_key="tag_count",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.tag_count,
            # Consider adding entity_registry_enabled_default=False here if deemed less popular
        ),
        PaperlessEntityDescription(
            key="correspondent_count",
            translation_key="correspondent_count",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.correspondent_count,
            # Consider adding entity_registry_enabled_default=False here if deemed less popular
        ),
        PaperlessEntityDescription(
            key="document_type_count",
            translation_key="document_type_count",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.document_type_count,
            # Consider adding entity_registry_enabled_default=False here if deemed less popular
        ),
    )

    # ... (rest of the file) ...
    ```

By making these changes, the identified less popular entities will not be automatically enabled when a user sets up the `paperless_ngx` integration. This aligns with the rule's goal of minimizing default resource usage and UI clutter, while still providing the full range of data to users who opt-in to see it.

_Created at 2025-05-27 13:07:50. Prompt tokens: 5506, Output tokens: 1751, Total tokens: 10740_
