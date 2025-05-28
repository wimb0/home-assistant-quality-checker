```markdown
# pegel_online: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates) |
| Status | **todo**                                                                 |

## Overview

This rule requires integrations to specify the number of parallel updates allowed for entities within a platform, especially to prevent overwhelming external services.

The `pegel_online` integration communicates with an external API (`aiopegelonline`) to fetch data for sensor entities. It uses a `DataUpdateCoordinator` (`homeassistant/components/pegel_online/coordinator.py`) to centralize the fetching of data for all entities belonging to a single station. The entities themselves (`homeassistant/components/pegel_online/sensor.py`) inherit from `CoordinatorEntity`, indicating they rely on the coordinator for data.

According to the rule's guidance for integrations using a coordinator for read-only platforms (like sensors), the `PARALLEL_UPDATES` constant should be set to `0` in the platform file (`sensor.py`). This signals that updates are handled by the coordinator and entity updates themselves do not perform blocking I/O that needs limiting.

Upon reviewing the provided code, the `sensor.py` file does not define the `PARALLEL_UPDATES` constant. While the coordinator handles the primary data fetching limiting potential concurrent requests *to the external API* during a single data update cycle, explicitly setting `PARALLEL_UPDATES = 0` in the platform file is still required by the rule to correctly indicate to Home Assistant's core that parallel entity updates within this platform are not a concern that needs framework-level limiting, as they rely on the shared coordinator data.

Therefore, the rule applies, and the integration currently does not fully follow it as it's missing the required constant definition in the sensor platform file.

## Suggestions

To comply with the `parallel-updates` rule, add the `PARALLEL_UPDATES` constant set to `0` in the `homeassistant/components/pegel_online/sensor.py` file. This explicitly signals that sensor entities within this platform do not perform individual blocking updates and rely on the shared data from the `DataUpdateCoordinator`.

Modify `homeassistant/components/pegel_online/sensor.py` as follows:

```python
"""PEGELONLINE sensor entities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from aiopegelonline.models import CurrentMeasurement, StationMeasurements

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PegelOnlineConfigEntry, PegelOnlineDataUpdateCoordinator
from .entity import PegelOnlineEntity

# Add this line:
PARALLEL_UPDATES = 0

@dataclass(frozen=True, kw_only=True)
class PegelOnlineSensorEntityDescription(SensorEntityDescription):
... rest of the file ...
```

Adding this line fulfills the rule's requirement for integrations using a coordinator on read-only platforms.
```

_Created at 2025-05-25 11:23:51. Prompt tokens: 5856, Output tokens: 777, Total tokens: 7430_
