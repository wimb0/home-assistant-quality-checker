```markdown
# pegel_online: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules) |
| Status | **done**                                                                 |

## Overview

The `common-modules` rule requires integrations to place common architectural patterns, specifically the `DataUpdateCoordinator` and any base entity class, into dedicated files named `coordinator.py` and `entity.py` respectively. This integration utilizes both of these patterns.

Upon reviewing the code:
*   The integration uses a `DataUpdateCoordinator` defined in `homeassistant/components/pegel_online/coordinator.py` named `PegelOnlineDataUpdateCoordinator`. This is confirmed by the import and usage in `__init__.py`.
*   The integration uses a base entity class defined in `homeassistant/components/pegel_online/entity.py` named `PegelOnlineEntity`. This is confirmed by the import and inheritance in `sensor.py`.

Both common patterns are correctly placed in their designated files according to the rule requirements.

## Suggestions

No suggestions needed. The integration fully follows the `common-modules` rule.
```

_Created at 2025-05-25 11:21:55. Prompt tokens: 5810, Output tokens: 313, Total tokens: 6670_
