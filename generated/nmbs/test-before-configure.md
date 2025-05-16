# nmbs: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-configure` rule requires integrations to test their connection to a device or service within the config flow before an entry is created. This ensures that users are immediately notified of issues like network problems, incorrect credentials, or API unavailability, preventing the setup of a non-functional integration.

The `nmbs` integration connects to the iRail cloud service to fetch train information. Therefore, this rule applies.

The integration adheres to this rule. In its `config_flow.py`:
1.  The `async_step_user` method, which handles the initial user setup, calls `self._fetch_stations_choices()`.
2.  `_fetch_stations_choices()` in turn calls `self._fetch_stations()`.
3.  The `_fetch_stations()` method initializes the `iRail` client and attempts to fetch the list of all available train stations using `await api_client.get_stations()`.
    ```python
    # config_flow.py
    async def _fetch_stations(self) -> list[StationDetails]:
        """Fetch the stations."""
        api_client = iRail(session=async_get_clientsession(self.hass))
        stations_response = await api_client.get_stations()
        if stations_response is None:
            raise CannotConnect("The API is currently unavailable.")
        return stations_response.stations
    ```
4.  If `api_client.get_stations()` fails (e.g., `stations_response` is `None`), a `CannotConnect` exception is raised.
5.  This exception is caught in `async_step_user`, and the config flow is aborted with the reason `"api_unavailable"`, informing the user of the problem:
    ```python
    # config_flow.py
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to setup a connection between 2 stations."""

        try:
            choices = await self._fetch_stations_choices()
        except CannotConnect:
            return self.async_abort(reason="api_unavailable")
        # ... rest of the method
    ```
This sequence ensures that a connection to the iRail API and the ability to fetch basic data is verified before the user is even presented with the form to select stations. If this initial connection test fails, the setup process stops, and the user is notified.

Similarly, the `async_step_import` method also performs this check:
```python
# config_flow.py
async def async_step_import(self, user_input: dict[str, Any]) -> ConfigFlowResult:
    """Import configuration from yaml."""
    try:
        self.stations = await self._fetch_stations()
    except CannotConnect:
        return self.async_abort(reason="api_unavailable")
    # ... rest of the method
```

This mechanism fulfills the requirement of testing the connection and providing feedback to the user if the connection fails during the configuration process.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:25:25. Prompt tokens: 10404, Output tokens: 807, Total tokens: 13446_
