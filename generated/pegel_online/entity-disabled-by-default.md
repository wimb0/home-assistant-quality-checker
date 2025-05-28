```markdown
# pegel_online: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default)                                                     |
| Status | **done**                                                                 |

## Overview

This rule requires integrations to disable less popular or noisy entities by default to conserve resources. The `pegel_online` integration creates sensor entities, making this rule applicable.

The integration follows this rule by utilizing the `entity_registry_enabled_default=False` attribute on the sensor entity descriptions. In the `homeassistant/components/pegel_online/sensor.py` file, within the `SENSORS` tuple that defines the available sensor types, most sensor descriptions explicitly set this attribute to `False`:

*   `air_temperature`
*   `oxygen_level`
*   `ph_value`
*   `water_speed`
*   `water_flow`
*   `water_temperature`

The primary sensor, `water_level`, which is expected to be the main reason for users to install this integration, does not have `entity_registry_enabled_default` set (meaning it defaults to `True`), which aligns with the rule's intent to keep popular entities enabled. The `clearance_height` sensor is also left enabled by default; while potentially less popular than `water_level`, this is a subjective decision permitted by the rule's guidance on popularity.

By disabling the majority of the supplementary sensors by default, the integration effectively manages resource usage for users who may only be interested in the core water level measurement, while still allowing others to enable the additional data points if needed.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:24:58. Prompt tokens: 5943, Output tokens: 437, Total tokens: 7457_
