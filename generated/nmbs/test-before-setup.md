# nmbs: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires that integrations check during their initialization (specifically within `async_setup_entry`) whether they can be set up correctly. This involves verifying connectivity to devices or services, validating API keys, etc., and raising appropriate exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) if issues are found. This provides immediate feedback to the user and allows Home Assistant to handle retries or re-authentication gracefully.

This rule applies to the `nmbs` integration as it relies on an external API (iRail) to fetch train connection and liveboard data. It's important to verify that the API is reachable and can provide data for the configured route when a config entry is being set up.

The `nmbs` integration partially addresses initial setup checks but does not fully comply with the rule for individual config entries:

1.  **Global Setup (`__init__.py:async_setup`)**:
    The global `async_setup` function attempts to fetch all available stations using `await api_client.get_stations()`. If this call fails (e.g., `station_response is None`), `async_setup` returns `False`. This effectively prevents the entire `nmbs` integration from loading if the basic station data cannot be retrieved from the API, which is a good initial safeguard.

2.  **Config Entry Setup (`__init__.py:async_setup_entry` and `sensor.py:async_setup_entry`)**:
    *   The `async_setup_entry` function in `__init__.py` simply forwards the setup to the sensor platform:
        ```python
        # __init__.py
        async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
            """Set up NMBS from a config entry."""
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
            return True
        ```
    *   The platform setup in `sensor.py:async_setup_entry` initializes the `iRail` API client and resolves the `station_from` and `station_to` details from data cached during the global `async_setup`.
        ```python
        # sensor.py
        async def async_setup_entry(
            hass: HomeAssistant,
            config_entry: ConfigEntry,
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            """Set up NMBS sensor entities based on a config entry."""
            api_client = iRail(session=async_get_clientsession(hass))
            # ...
            station_from = find_station(hass, config_entry.data[CONF_STATION_FROM])
            station_to = find_station(hass, config_entry.data[CONF_STATION_TO])
            # ...
            async_add_entities([...])
        ```
        Crucially, this function does **not** make an actual API call to test if connections or liveboard data can be fetched for the *specific route* defined in the config entry (e.g., by attempting an initial `await api_client.get_connections(...)`).

The problem is that if the global `get_stations()` call succeeds, but fetching data for a *specific route* (e.g., from station A to station B) fails due to a temporary API issue or an issue specific to that route, the `async_setup_entry` will still complete successfully. The failure will only be apparent when the sensor entities try to perform their first update (in `NMBSSensor.async_update` or `NMBSLiveBoard.async_update`), by which time the setup is already considered successful by Home Assistant.

This behavior means the user isn't immediately notified of a setup problem for that specific entry (e.g., with a "Retrying setup" message), and Home Assistant doesn't automatically retry the setup if `ConfigEntryNotReady` were raised. The integration does not use a `DataUpdateCoordinator` whose `async_config_entry_first_refresh` could implicitly handle this.

Therefore, the integration does not fully follow the `test-before-setup` rule, as it misses the opportunity to test the specific configuration of an entry during `async_setup_entry` and raise appropriate exceptions.

## Suggestions

To make the `nmbs` integration compliant with the `test-before-setup` rule, an initial API call should be made within the platform's `async_setup_entry` function (in `sensor.py`) to verify that data for the configured route can be fetched.

1.  **Modify `sensor.py:async_setup_entry`**:
    After initializing `api_client` and resolving `station_from` and `station_to`, add a test API call. This call should attempt to fetch connection data for the configured route.

2.  **Handle API Responses and Exceptions**:
    Wrap the test API call in a `try...except` block to catch potential errors.
    *   If the API call indicates a temporary issue (e.g., network error, API server error, no data returned for a usually valid route), raise `ConfigEntryNotReady`. This will prompt Home Assistant to retry the setup later.
    *   The `pyrail` library's `get_connections` method returns `Connections | None`. If `None` is returned, or if an underlying `aiohttp.ClientError` (or similar network exception) occurs, this should be treated as a condition for `ConfigEntryNotReady`.

**Example Implementation Snippet for `sensor.py`:**

```python
# sensor.py
import aiohttp # Ensure aiohttp.ClientError is available if pyrail can raise it directly or indirectly
# ... other imports
from homeassistant.exceptions import ConfigEntryNotReady

# ...

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up NMBS sensor entities based on a config entry."""
    api_client = iRail(session=async_get_clientsession(hass))

    name = config_entry.data.get(CONF_NAME, None)
    show_on_map = config_entry.data.get(CONF_SHOW_ON_MAP, False)
    excl_vias = config_entry.data.get(CONF_EXCLUDE_VIAS, False)

    station_from = find_station(hass, config_entry.data[CONF_STATION_FROM])
    station_to = find_station(hass, config_entry.data[CONF_STATION_TO])

    # If stations are not found in the cached data (e.g., data became stale or invalid ID),
    # this could also be a point to raise ConfigEntryError, though find_station currently
    # returns None, and subsequent code would likely fail. Explicit check might be better.
    if not station_from or not station_to:
        _LOGGER.error(
            "Could not find configured stations: From '%s', To '%s'. Please reconfigure.",
            config_entry.data[CONF_STATION_FROM],
            config_entry.data[CONF_STATION_TO],
        )
        # This scenario might be better as ConfigEntryError if stations are truly invalid
        # rather than a temporary API issue for a valid route.
        # However, find_station uses pre-loaded data. Config flow should prevent invalid station IDs.
        # For this rule, we focus on API connectivity for validated stations.
        pass # Assuming station_from/to are valid if code reaches here due to config flow validation

    # Test API connectivity for the specific route
    try:
        _LOGGER.debug(
            "Testing API connection for route: %s to %s",
            station_from.standard_name,
            station_to.standard_name,
        )
        initial_connections = await api_client.get_connections(
            station_from.id, station_to.id
        )
        if initial_connections is None: # pyrail returns None on failure to get data
            _LOGGER.warning(
                "NMBS API did not return connection data for route %s to %s during setup. Will retry.",
                station_from.standard_name,
                station_to.standard_name,
            )
            raise ConfigEntryNotReady(
                f"Failed to retrieve initial connection data for route {station_from.standard_name} to {station_to.standard_name}"
            )
    except aiohttp.ClientError as ex: # Catch network errors from aiohttp if pyrail doesn't wrap them
        _LOGGER.warning(
            "NMBS API request failed for route %s to %s during setup: %s. Will retry.",
            station_from.standard_name,
            station_to.standard_name,
            ex,
        )
        raise ConfigEntryNotReady(
            f"API request failed for route {station_from.standard_name} to {station_to.standard_name}: {ex}"
        ) from ex
    # Add any other pyrail specific exceptions if they exist for temporary failures

    _LOGGER.debug(
        "API connection test successful for route: %s to %s",
        station_from.standard_name,
        station_to.standard_name,
    )

    # Proceed with entity setup if the test call was successful
    async_add_entities(
        [
            NMBSSensor(
                api_client, name, show_on_map, station_from, station_to, excl_vias
            ),
            NMBSLiveBoard(
                api_client, station_from, station_from, station_to, excl_vias
            ),
            NMBSLiveBoard(api_client, station_to, station_from, station_to, excl_vias),
        ]
    )
```

By implementing this check, the integration will:
*   Provide immediate feedback if a configured route cannot be initialized due to temporary API issues.
*   Allow Home Assistant to automatically retry the setup, improving user experience.
*   Align with the `test-before-setup` quality scale rule.

_Created at 2025-05-11 07:26:55. Prompt tokens: 9781, Output tokens: 2401, Total tokens: 18064_
