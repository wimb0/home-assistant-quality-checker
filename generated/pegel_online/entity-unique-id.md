# pegel_online: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that all entities created by the integration have a unique ID. This allows users to customize entities and Home Assistant to track them across restarts via the entity registry.

The `pegel_online` integration creates sensor entities as defined in `homeassistant/components/pegel_online/sensor.py`. The rule `entity-unique-id` is therefore applicable to this integration.

Upon reviewing the code, the `PegelOnlineSensor` class, which represents the sensors provided by the integration, sets the `_attr_unique_id` attribute in its `__init__` method:

```python
# homeassistant/components/pegel_online/sensor.py
class PegelOnlineSensor(PegelOnlineEntity, SensorEntity):
    """Representation of a PEGELONLINE sensor."""

    entity_description: PegelOnlineSensorEntityDescription

    def __init__(
        self,
        coordinator: PegelOnlineDataUpdateCoordinator,
        description: PegelOnlineSensorEntityDescription,
    ) -> None:
        """Initialize a PEGELONLINE sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self.station.uuid}_{description.key}" # <-- Unique ID is set
        # ... rest of init
```

The unique ID is constructed using the station's UUID (`self.station.uuid`) and the sensor description's key (`description.key`). The station UUID is unique per configured station, and the sensor description key is unique per type of measurement for that station. This combination creates a unique identifier for each sensor entity created by the integration, satisfying the requirements of the rule.

The integration correctly implements the `entity-unique-id` rule.

## Suggestions

No suggestions needed. The integration correctly follows the rule.

_Created at 2025-05-25 11:22:18. Prompt tokens: 5798, Output tokens: 516, Total tokens: 6951_
