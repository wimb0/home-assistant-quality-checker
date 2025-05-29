# jewish_calendar: inject-websession

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [inject-websession](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession)                                                     |
| Status | **exempt**                                       |
| Reason | The integration performs local calculations and does not make HTTP requests to external services. |

## Overview

The `inject-websession` rule requires integrations that make HTTP requests to use a shared web session provided by Home Assistant (via `async_get_clientsession` for `aiohttp` or `get_async_client` for `httpx`) or to create a new session using Home Assistant's helpers if a shared session is not appropriate. This is to improve the efficiency of web sessions. The rule explicitly states: "If the integration is not making any HTTP requests, this rule does not apply."

The `jewish_calendar` integration is designed to provide sensors and services related to the Jewish calendar. Its core functionality relies on the `hdate` Python library, as specified in its `manifest.json`:
```json
{
  "domain": "jewish_calendar",
  "name": "Jewish Calendar",
  "codeowners": ["@tsvi"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/jewish_calendar",
  "iot_class": "calculated",
  "loggers": ["hdate"],
  "requirements": ["hdate[astral]==1.1.0"],
  "single_config_entry": true
}
```
The `hdate` library, along with its `astral` dependency (for sun-based calculations like sunrise/sunset), performs calculations locally based on date, time, and location.

A review of the integration's code (`__init__.py`, `sensor.py`, `binary_sensor.py`, `service.py`, etc.) shows that it instantiates and uses objects from the `hdate` library (e.g., `hdate.Location`, `hdate.Zmanim`, `hdate.HDateInfo`, `hdate.HebrewDate`, `hdate.Omer`). For example, in `__init__.py`:
```python
    location = await hass.async_add_executor_job(
        partial(
            Location,
            name=hass.config.location_name,
            # ... other parameters
        )
    )
```
And in `entity.py`:
```python
    def make_zmanim(self, date: dt.date) -> Zmanim:
        """Create a Zmanim object."""
        return Zmanim(
            date=date,
            location=self.data.location,
            candle_lighting_offset=self.data.candle_lighting_offset,
            havdalah_offset=self.data.havdalah_offset,
        )
```
These operations are computational and do not involve network communication with external HTTP services. The integration also uses `homeassistant.helpers.sun.get_astral_event_date`, which relies on the `astral` library for local astronomical calculations, and `zoneinfo.available_timezones` from the Python standard library for timezone information, neither of which make HTTP requests in this context.

The `iot_class` being "calculated" further supports that this integration operates by performing calculations rather than by communicating with external devices or cloud services via HTTP.

Since the `jewish_calendar` integration and its primary dependency `hdate` do not make HTTP requests to external services, the `inject-websession` rule does not apply.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:34:52. Prompt tokens: 13365, Output tokens: 863, Total tokens: 15566_
