```markdown
# pegel_online: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                                                 |

## Overview

The `test-before-configure` rule requires integrations that connect to external services to perform a connection test during the configuration flow. This helps identify issues like connectivity problems or incorrect input early, improving the user experience.

The `pegel_online` integration connects to the PEGELONLINE API to retrieve water level data. Therefore, this rule applies to the integration.

The integration **follows** this rule. In the `config_flow.py` file, specifically within the `async_step_user` method, the integration attempts to connect to the PEGELONLINE API and fetch nearby stations based on the user's location and radius input.

As seen in `homeassistant/components/pegel_online/config_flow.py`, lines 44-49, the code performs the following:

```python
api = PegelOnline(async_get_clientsession(self.hass))
try:
    stations = await api.async_get_nearby_stations(
        user_input[CONF_LOCATION][CONF_LATITUDE],
        user_input[CONF_LOCATION][CONF_LONGITUDE],
        user_input[CONF_RADIUS],
    )
except CONNECT_ERRORS:
    return self._show_form_user(user_input, errors={"base": "cannot_connect"})
```

This code creates an API client and immediately attempts to call `async_get_nearby_stations`. If a `CONNECT_ERRORS` exception occurs during this call, it catches the error and returns the configuration form (`_show_form_user`) with a base error message indicating a connection failure. This successfully tests the connectivity and handles potential connection issues before allowing the user to proceed with selecting a station or creating the config entry, thus fulfilling the requirements of the `test-before-configure` rule.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:22:40. Prompt tokens: 6105, Output tokens: 517, Total tokens: 7692_
