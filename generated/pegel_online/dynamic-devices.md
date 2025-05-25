```markdown
# pegel_online: dynamic-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [dynamic-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices) |
| Status | **exempt**                                                               |
| Reason | The integration is configured for a single, user-selected station and does not dynamically discover or add new stations (devices) after setup. |

## Overview

The `dynamic-devices` rule requires integrations that can discover new devices or entities after the initial setup to automatically create corresponding entities in Home Assistant when those devices appear. This is typically implemented by listening for updates from a coordinator and adding new entities based on the updated data.

This rule does not apply to the `pegel_online` integration. The integration's configuration flow (`homeassistant/components/pegel_online/config_flow.py`) guides the user to select a *single* specific water measuring station based on location and radius search. Once configured, the integration monitors only this chosen station using the `PegelOnlineDataUpdateCoordinator` (`homeassistant/components/pegel_online/coordinator.py`).

The `sensor.py` file (`homeassistant/components/pegel_online/sensor.py`) sets up sensor entities (`PegelOnlineSensor`) based on the *available measurements* for this *single, pre-selected station* during the `async_setup_entry` function.

```python
async def async_setup_entry(
    hass: HomeAssistant,
    entry: PegelOnlineConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the PEGELONLINE sensor."""
    coordinator = entry.runtime_data

    async_add_entities(
        [
            PegelOnlineSensor(coordinator, description)
            for description in SENSORS
            if description.measurement_fn(coordinator.data) is not None
        ]
    )
```
This code iterates through a predefined list of potential sensors (`SENSORS`) and adds one entity for each sensor type *if* that measurement is present in the data for the configured station at setup time. It does not include mechanisms to detect entirely *new stations* (which would represent new devices in HA) that might become available later or to dynamically add entities representing those new stations.

Since the integration's design is focused on monitoring a single, static station selection rather than discovering and adding multiple stations dynamically, the `dynamic-devices` rule is not applicable.

## Suggestions

No suggestions needed. The rule does not apply to this integration's current design.
```

_Created at 2025-05-25 11:24:34. Prompt tokens: 6036, Output tokens: 614, Total tokens: 7532_
