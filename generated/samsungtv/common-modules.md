```markdown
# samsungtv: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **done**                                                                 |

## Overview

This rule requires integrations to place common code patterns, specifically the Data Update Coordinator and base Entity classes, into dedicated `coordinator.py` and `entity.py` files, respectively.

The `samsungtv` integration fully follows this rule.

The `SamsungTVDataUpdateCoordinator` class, which handles fetching data for the integration, is correctly defined in `homeassistant/components/samsungtv/coordinator.py`. This aligns with the rule's requirement for the coordinator to reside in this file.

The base entity class, `SamsungTVEntity`, which provides common functionality for the integration's entities (media player and remote), is defined in `homeassistant/components/samsungtv/entity.py`. This also conforms to the rule's requirement for the base entity class location.

By adhering to this structure, the integration improves consistency with other Home Assistant integrations, making the code easier for developers to navigate and understand.

No suggestions needed.
```

_Created at 2025-05-25 11:27:51. Prompt tokens: 30048, Output tokens: 311, Total tokens: 30675_
