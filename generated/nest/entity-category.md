# nest: entity-category

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [entity-category](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-category)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-category` rule requires that entities are assigned an appropriate `EntityCategory` (e.g., `CONFIG` or `DIAGNOSTIC`) when the default category (implying a primary entity) is inappropriate. This helps in correct classification and identification, especially for auto-generated dashboards.

The Nest integration creates several types of entities:
*   **Sensors** (`sensor.py`): `TemperatureSensor` and `HumiditySensor`. These report primary environmental data.
*   **Climate** (`climate.py`): `ThermostatEntity`. This provides primary control and status for thermostats.
*   **Camera** (`camera.py`): `NestRTSPEntity` and `NestWebRTCEntity`. These provide primary camera feeds.
*   **Event** (`event.py`): `NestTraitEventEntity`. These report primary device events like doorbell chimes or motion.

A review of the code for these entity platforms (`sensor.py`, `climate.py`, `camera.py`, `event.py`) shows that none of the entity classes explicitly set the `_attr_entity_category` attribute. This means all entities created by the Nest integration will have the default entity category (`None`).

The default entity category is appropriate for entities that represent the primary state, control, or data of a device. All entities created by the Nest integration fall into this description:
*   Temperature and humidity sensors provide direct, primary measurements.
*   Thermostat entities provide primary climate control and status.
*   Camera entities provide primary video streams.
*   Event entities report primary device occurrences (e.g., motion, doorbell press).

The Nest integration does not appear to create entities that would be considered purely for configuration of the integration/device (which would warrant `EntityCategory.CONFIG`) or purely for diagnostics about the integration/device's health or status (which would warrant `EntityCategory.DIAGNOSTIC`). Diagnostic information is provided through the dedicated diagnostics platform (`diagnostics.py`), not through specific diagnostic entities.

Since the default entity category is appropriate for all entities currently created by the Nest integration, the integration correctly follows this rule by allowing its entities to use the default category.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:07:54. Prompt tokens: 32069, Output tokens: 582, Total tokens: 34731_
