# nmbs: has-entity-name

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [has-entity-name](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `has-entity-name` rule mandates that all entities should set the `_attr_has_entity_name = True` attribute. This allows Home Assistant to consistently manage and display entity names, potentially in conjunction with device names, for a better user experience.

This rule applies to the `nmbs` integration as it creates sensor entities (`NMBSSensor` and `NMBSLiveBoard`) in `sensor.py`.

Currently, the `nmbs` integration does not comply with this rule.
The entity classes `NMBSSensor` and `NMBSLiveBoard` do not set `_attr_has_entity_name = True`. Instead, they define a `name` property to provide their names.

**Code evidence from `sensor.py`:**

For `NMBSSensor`:
```python
class NMBSSensor(SensorEntity):
    # _attr_has_entity_name = True is missing

    # ...
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        if self._name is None: # self._name is derived from config_entry or YAML
            return f"Train from {self._station_from.standard_name} to {self._station_to.standard_name}"
        return self._name
```

For `NMBSLiveBoard`:
```python
class NMBSLiveBoard(SensorEntity):
    # _attr_has_entity_name = True is missing

    # ...
    @property
    def name(self) -> str:
        """Return the sensor default name."""
        return f"Trains in {self._station.standard_name}"
```

To comply with the rule, these entities need to adopt `_attr_has_entity_name = True` and set their names using `_attr_name` (typically in the `__init__` method), rather than relying on a `name` property.

## Suggestions

To make the `nmbs` integration compliant with the `has-entity-name` rule, the following changes should be made in `sensor.py`:

1.  **For the `NMBSSensor` class:**
    *   Add the class attribute `_attr_has_entity_name = True`.
    *   In the `__init__` method, set `self._attr_name` based on the logic currently in the `name` property.
    *   Remove the `name(self)` property.

    ```python
    # sensor.py
    class NMBSSensor(SensorEntity):
        _attr_has_entity_name = True  # Add this line
        _attr_attribution = "https://api.irail.be/"
        _attr_native_unit_of_measurement = UnitOfTime.MINUTES

        def __init__(
            self,
            api_client: iRail,
            name: str | None,  # Name from config_entry.data.get(CONF_NAME, None) or YAML
            show_on_map: bool,
            station_from: StationDetails,
            station_to: StationDetails,
            excl_vias: bool,
        ) -> None:
            """Initialize the NMBS connection sensor."""
            self._show_on_map = show_on_map
            self._api_client = api_client
            self._station_from = station_from
            self._station_to = station_to
            self._excl_vias = excl_vias

            # Set _attr_name based on the logic from the old name property
            if name is None:  # For UI-configured entries, name is None
                self._attr_name = f"Train from {self._station_from.standard_name} to {self._station_to.standard_name}"
            else: # For YAML-imported entries, name could be user-set or default "NMBS"
                self._attr_name = name

            # The unique_id is handled by the unique_id property, no changes needed here for it.
            # self._attr_unique_id = f"nmbs_connection_{self._station_from.id}_{self._station_to.id}{'_excl_vias' if self._excl_vias else ''}"

            self._attrs: ConnectionDetails | None = None
            self._state = None

        # Remove the name property as _attr_name is now used
        # @property
        # def name(self) -> str:
        #     """Return the name of the sensor."""
        #     if self._name is None:
        #         return f"Train from {self._station_from.standard_name} to {self._station_to.standard_name}"
        #     return self._name

        # ... (rest of the class)
    ```

2.  **For the `NMBSLiveBoard` class:**
    *   Add the class attribute `_attr_has_entity_name = True`.
    *   In the `__init__` method, set `self._attr_name` based on the logic currently in the `name` property.
    *   Remove the `name(self)` property.

    ```python
    # sensor.py
    class NMBSLiveBoard(SensorEntity):
        _attr_has_entity_name = True  # Add this line
        _attr_attribution = "https://api.irail.be/"
        # _attr_name will be set in __init__

        def __init__(
            self,
            api_client: iRail,
            live_station: StationDetails,
            station_from: StationDetails, # context for unique_id
            station_to: StationDetails,   # context for unique_id
            excl_vias: bool,
        ) -> None:
            """Initialize the sensor for getting liveboard data."""
            self._station = live_station # This is the station for the liveboard
            self._api_client = api_client
            # These are for unique_id generation
            self._station_from = station_from
            self._station_to = station_to

            self._excl_vias = excl_vias
            self._attrs: LiveboardDeparture | None = None
            self._state: str | None = None

            self.entity_registry_enabled_default = False

            # Set _attr_name based on the logic from the old name property
            self._attr_name = f"Trains in {self._station.standard_name}"

            # The unique_id is handled by the unique_id property, no changes needed here for it.
            # self._attr_unique_id = f"nmbs_live_{self._station.id}_{self._station_from.id}_{self._station_to.id}{'_excl_vias' if self._excl_vias else ''}"

        # Remove the name property as _attr_name is now used
        # @property
        # def name(self) -> str:
        #     """Return the sensor default name."""
        #     return f"Trains in {self._station.standard_name}"

        # ... (rest of the class)
    ```

By implementing these changes, the entities will correctly declare `_attr_has_entity_name = True` and provide their specific names via `_attr_name`, adhering to the rule's requirements for standardized entity naming. This allows Home Assistant to better manage how entity names are generated and displayed, especially if devices are introduced in the future.

_Created at 2025-05-11 07:23:45. Prompt tokens: 9920, Output tokens: 1813, Total tokens: 20438_
