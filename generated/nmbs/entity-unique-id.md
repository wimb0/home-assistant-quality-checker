# nmbs: entity-unique-id

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [entity-unique-id](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unique-id)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-unique-id` rule requires that all entities created by an integration have a unique ID. This allows Home Assistant to track entities across restarts and enables users to customize them (e.g., rename, change unit of measurement).

This rule **applies** to the `nmbs` integration because it creates `sensor` entities to represent train connections and liveboard information.

The `nmbs` integration **fully follows** this rule. Both entity classes defined in `sensor.py` implement the `unique_id` property:

1.  **`NMBSLiveBoard(SensorEntity)`:**
    This class, representing live train departures from a station, defines its unique ID as follows:
    ```python
    # sensor.py
    @property
    def unique_id(self) -> str:
        """Return the unique ID."""

        unique_id = f"{self._station.id}_{self._station_from.id}_{self._station_to.id}"
        vias = "_excl_vias" if self._excl_vias else ""
        return f"nmbs_live_{unique_id}{vias}"
    ```
    This ID is constructed using the unique IDs of the live station, the "from" station, and the "to" station, along with a flag indicating if via routes are excluded. The prefix `nmbs_live_` further ensures uniqueness.

2.  **`NMBSSensor(SensorEntity)`:**
    This class, representing a specific train connection between two stations, defines its unique ID as follows:
    ```python
    # sensor.py
    @property
    def unique_id(self) -> str:
        """Return the unique ID."""
        unique_id = f"{self._station_from.id}_{self._station_to.id}"

        vias = "_excl_vias" if self._excl_vias else ""
        return f"nmbs_connection_{unique_id}{vias}"
    ```
    This ID is constructed using the unique IDs of the "from" station and the "to" station, along with a flag indicating if via routes are excluded. The prefix `nmbs_connection_` ensures uniqueness.

In both cases, the unique IDs are derived from stable, unique identifiers (station IDs obtained from the `pyrail` library) and configuration options, ensuring that each entity instance has a distinct and persistent identifier. The `config_flow.py` also handles unique ID generation for config entries and includes logic for migrating older entity IDs to the new format, further demonstrating correct handling of unique identifiers.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:22:04. Prompt tokens: 9176, Output tokens: 696, Total tokens: 11527_
