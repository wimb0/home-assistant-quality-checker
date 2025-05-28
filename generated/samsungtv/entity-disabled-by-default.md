```markdown
# samsungtv: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule recommends that integrations disable less popular or noisy entities by default to conserve system resources related to state history tracking. The `samsungtv` integration provides core entities for controlling a Samsung TV: a `media_player` entity and a `remote` entity.

Based on the code provided:

1.  The `media_player` entity is defined in `homeassistant/components/samsungtv/media_player.py` as `SamsungTVDevice`. It does not explicitly set `_attr_entity_registry_enabled_default = False`.
2.  The `remote` entity is defined in `homeassistant/components/samsungtv/remote.py` as `SamsungTVRemote`. It also does not explicitly set `_attr_entity_registry_enabled_default = False`.

Both `media_player` and `remote` entities are primary entities for a TV integration and are considered highly popular and essential for user interaction. They are not typically categorized as "less popular" or excessively "noisy" compared to, for example, a signal strength sensor (as shown in the rule's example).

Therefore, the integration correctly keeps its primary entities enabled by default, aligning with the intent of the `entity-disabled-by-default` rule, which is to target *less popular* or *noisy* entities, not core functional ones.

## Suggestions

No suggestions needed. The integration correctly handles the default enablement of its entities based on their popularity and function.
```

_Created at 2025-05-25 11:31:52. Prompt tokens: 30181, Output tokens: 441, Total tokens: 31485_
