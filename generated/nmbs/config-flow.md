# nmbs: config-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [config-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `config-flow` rule mandates that integrations must be configurable through the Home Assistant UI using a config flow. This includes using appropriate selectors, validating input, providing clear descriptions via `strings.json`, and correctly storing configuration in `ConfigEntry.data` (for connection-critical parameters) and `ConfigEntry.options` (for settings not essential for establishing the connection).

The `nmbs` integration largely adheres to this rule:

1.  **Config Flow Enabled:** The `manifest.json` correctly sets `"config_flow": true`.
2.  **Config Flow Implementation:** A `config_flow.py` file exists, defining `NMBSConfigFlow` which handles the user setup process (`async_step_user`) and YAML import (`async_step_import`).
3.  **User-Friendly UI:**
    *   It uses `SelectSelector` for `CONF_STATION_FROM` and `CONF_STATION_TO`, allowing users to choose from a dynamically fetched list of stations. This is a good use of selectors.
    *   It uses `BooleanSelector` for `CONF_EXCLUDE_VIAS` and `CONF_SHOW_ON_MAP`.
    *   Input validation is present, for example, to ensure the departure and arrival stations are not the same (`errors["base"] = "same_station"` in `config_flow.py`).
    *   The `strings.json` file includes `config.step.user.data` for field labels and `config.step.user.data_description` for contextual help, enhancing understandability.

However, there is one area where the integration does not fully align with the rule's requirements regarding configuration storage:

*   **Configuration Storage (`ConfigEntry.data` vs. `ConfigEntry.options`):**
    The rule states: "The integration should store all configuration in the `ConfigEntry.data` field, while all settings that are not needed for the connection to be made should be stored in the `ConfigEntry.options` field."
    Currently, all user inputs from the setup flow (`CONF_STATION_FROM`, `CONF_STATION_TO`, `CONF_EXCLUDE_VIAS`, `CONF_SHOW_ON_MAP`) are stored in `ConfigEntry.data`.
    *   `CONF_STATION_FROM` and `CONF_STATION_TO` are essential for defining the route and fetching data, so they correctly belong in `ConfigEntry.data`.
    *   `CONF_EXCLUDE_VIAS` influences the type of connections fetched and is part of the unique ID generation for the config entry and sensors. Storing it in `ConfigEntry.data` is reasonable.
    *   `CONF_SHOW_ON_MAP` is a boolean flag that determines if the station's coordinates are added as attributes to the sensor for display on a map. This setting is not required for the integration to establish a connection or fetch train data. It is purely a presentational setting. As such, it should be stored in `ConfigEntry.options` and be configurable via an options flow after the initial setup. The integration currently lacks an options flow.

Because `CONF_SHOW_ON_MAP` is stored in `data` instead of `options` and there is no options flow to modify it post-setup, the integration does not fully comply with this aspect of the rule.

## Suggestions

To fully comply with the `config-flow` rule, specifically regarding the storage of settings not essential for the connection:

1.  **Implement an Options Flow:**
    *   Add an options flow handler to `config_flow.py`. This typically involves creating a class that inherits from `config_entries.OptionsFlow` or by adding `async_step_options` to the existing `NMBSConfigFlow` class.
    *   This options flow should allow users to modify settings like `CONF_SHOW_ON_MAP` after the integration has been set up.

    **Example `config_flow.py` additions:**
    ```python
    from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
    from homeassistant.core import callback # Add this import

    # ... (existing imports)

    # At the end of NMBSConfigFlow or as a separate class:
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return NMBSOptionsFlowHandler(config_entry)

    class NMBSOptionsFlowHandler(OptionsFlow):
        """Handle NMBS options."""

        def __init__(self, config_entry: ConfigEntry) -> None:
            """Initialize options flow."""
            self.config_entry = config_entry

        async def async_step_init(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            """Manage the options."""
            if user_input is not None:
                return self.async_create_entry(title="", data=user_input)

            # Retrieve current value of CONF_SHOW_ON_MAP from options,
            # defaulting to value from data if not yet in options (for migration)
            # or a default like False.
            show_on_map_default = self.config_entry.options.get(
                CONF_SHOW_ON_MAP, self.config_entry.data.get(CONF_SHOW_ON_MAP, False)
            )

            schema = vol.Schema(
                {
                    vol.Optional(
                        CONF_SHOW_ON_MAP,
                        default=show_on_map_default,
                    ): BooleanSelector(),
                }
            )

            return self.async_show_form(
                step_id="init",
                data_schema=schema,
            )
    ```

2.  **Modify Initial Setup to Store `CONF_SHOW_ON_MAP` in Options:**
    *   When creating the config entry in `async_step_user`, separate `CONF_SHOW_ON_MAP` from the main `data` payload and pass it as `options`.

    **Example change in `config_flow.py`'s `async_step_user`:**
    ```python
    # ...
                if user_input is not None:
                    # ... (existing validation and unique ID setup) ...

                    data_payload = {
                        CONF_STATION_FROM: user_input[CONF_STATION_FROM],
                        CONF_STATION_TO: user_input[CONF_STATION_TO],
                        CONF_EXCLUDE_VIAS: user_input.get(CONF_EXCLUDE_VIAS, False),
                    }
                    options_payload = {
                        CONF_SHOW_ON_MAP: user_input.get(CONF_SHOW_ON_MAP, False),
                    }

                    config_entry_name = f"Train from {station_from.standard_name} to {station_to.standard_name}"
                    return self.async_create_entry(
                        title=config_entry_name,
                        data=data_payload,
                        options=options_payload, # Pass options here
                    )
    # ...
    ```
    *Note: When `CONF_SHOW_ON_MAP` is moved to `options` during initial setup, the data schema for the `user` step might only present it as `vol.Optional`. The default value for `CONF_SHOW_ON_MAP` if not provided by the user should be handled consistently.*

3.  **Update Sensor Entity to Read from Options:**
    *   In `sensor.py`, modify the `NMBSSensor` entity to read `CONF_SHOW_ON_MAP` from `self.config_entry.options` instead of `self.config_entry.data`.

    **Example change in `sensor.py`'s `async_setup_entry`:**
    ```python
    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up NMBS sensor entities based on a config entry."""
        api_client = iRail(session=async_get_clientsession(hass))

        name = config_entry.data.get(CONF_NAME, None) # Assuming CONF_NAME remains in data
        # Read CONF_SHOW_ON_MAP from options, falling back to data for existing entries
        # or a default.
        show_on_map = config_entry.options.get(
            CONF_SHOW_ON_MAP, config_entry.data.get(CONF_SHOW_ON_MAP, False)
        )
        excl_vias = config_entry.data.get(CONF_EXCLUDE_VIAS, False) # Remains in data

        station_from = find_station(hass, config_entry.data[CONF_STATION_FROM])
        station_to = find_station(hass, config_entry.data[CONF_STATION_TO])

        # ...
        async_add_entities(
            [
                NMBSSensor(
                    api_client, name, show_on_map, station_from, station_to, excl_vias
                ),
                # ...
            ]
        )
    ```
    And in `NMBSSensor` constructor:
    ```python
    class NMBSSensor(SensorEntity):
        # ...
        def __init__(
            self,
            api_client: iRail,
            name: str | None, # name could be None if not set in initial config
            show_on_map: bool, # Passed directly
            station_from: StationDetails,
            station_to: StationDetails,
            excl_vias: bool,
        ) -> None:
            """Initialize the NMBS connection sensor."""
            self._name = name
            self._show_on_map = show_on_map # Use the passed value
            # ...
    ```

4.  **Update `strings.json` for Options Flow:**
    *   If you implement an options flow, add corresponding entries in `strings.json` under an `options` key (similar to the `config` key) for any text displayed in the options UI.
    ```json
    {
      "config": { ... },
      "options": {
        "step": {
          "init": {
            "title": "NMBS Options",
            "data": {
              "show_on_map": "Display on map"
            },
            "data_description": {
              "show_on_map": "Show the station on the map."
            }
          }
        }
      },
      "issues": { ... }
    }
    ```

By making these changes, `CONF_SHOW_ON_MAP` will be correctly managed as an option, allowing users to modify it post-setup without re-configuring the entire entry, and bringing the integration into full compliance with the `config-flow` rule's storage requirements.

_Created at 2025-05-11 07:21:19. Prompt tokens: 10776, Output tokens: 2583, Total tokens: 16512_
