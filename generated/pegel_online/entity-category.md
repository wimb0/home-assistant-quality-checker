```markdown
# pegel_online: entity-category

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [entity-category](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-category)                                                     |
| Status | **done**                                                                 |

## Overview

The rule `entity-category` requires that entities are assigned an appropriate `EntityCategory` when the default category (which is `None`) is not suitable, typically for diagnostic or configuration entities.

The `pegel_online` integration provides sensor entities representing measurements such as water level, temperature, flow, etc. These are the primary data points offered by the integration. Looking at the code in `sensor.py`, the `PegelOnlineSensor` class inherits from `PegelOnlineEntity`. The `PegelOnlineEntity` class (defined in `entity.py`) sets various attributes like `_attr_has_entity_name`, `_attr_extra_state_attributes`, and `_attr_device_info`, but it does not set `_attr_entity_category`. Consequently, the sensors created by this integration will have the default `EntityCategory` of `None`.

The default `EntityCategory.NONE` is appropriate for entities that represent the core functionality and data the user is interested in, and which should be displayed prominently in dashboards and the main entity list. The sensors provided by this integration fit this description (e.g., `water_level`, `water_temperature`). There are no diagnostic or configuration sensors that would require a different category like `DIAGNOSTIC` or `CONFIG`.

Therefore, the integration correctly utilizes the default entity category where it is appropriate, fulfilling the requirement of the rule.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:24:40. Prompt tokens: 5605, Output tokens: 420, Total tokens: 6786_
