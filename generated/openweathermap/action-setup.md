# openweathermap: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [openweathermap](https://www.home-assistant.io/integrations/openweathermap/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `action-setup` rule requires that service actions provided by an integration are registered within the `async_setup` function of the integration's `__init__.py` file. This ensures that service definitions are available even if a specific configuration entry is not loaded, allowing for better validation of automations and more informative error messages to the user if a service call cannot be executed due to an unloaded entry.

This rule applies to the `openweathermap` integration because it defines a custom service, `get_minute_forecast`.

The `openweathermap` integration currently does **not** follow this rule.
1.  The integration does not have an `async_setup` function in its main `homeassistant/components/openweathermap/__init__.py` file.
2.  The `get_minute_forecast` service is registered as an entity service within the `async_setup_entry` function of the `weather` platform (in `homeassistant/components/openweathermap/weather.py`):
    ```python
    # homeassistant/components/openweathermap/weather.py
    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: OpenweathermapConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        # ...
        platform = entity_platform.async_get_current_platform()
        platform.async_register_entity_service( # <--- Service registered here
            name=SERVICE_GET_MINUTE_FORECAST,
            schema=None, 
            func="async_get_minute_forecast",
            supports_response=SupportsResponse.ONLY,
        )
    ```
    This method of registration means that the service action (for entities of a specific config entry) is only registered if that config entry successfully loads and sets up the weather platform. If a config entry fails to load, the service associated with its entities will not be registered. Consequently, automations targeting such a service might fail with a generic "service not found" error, rather than a more specific `ServiceValidationError` from the service itself explaining that the underlying entry is not loaded, which is the behavior preferred by the rule.

## Suggestions

To make the `openweathermap` integration compliant with the `action-setup` rule, the `get_minute_forecast` service should be re-implemented as a domain service and registered in `async_setup`.

1.  **Create `async_setup` in `__init__.py`:**
    Add an `async_setup(hass: HomeAssistant, config: ConfigType) -> bool:` function to `homeassistant/components/openweathermap/__init__.py`.

2.  **Register the service as a domain service:**
    Move the service registration logic from `weather.py` to the new `async_setup` function. This involves changing it from an entity service to a domain service using `hass.services.async_register`.

3.  **Define a service schema:**
    The new domain service will need to accept a target, typically an `entity_id` of an OpenWeatherMap weather entity, or a `config_entry_id`. Define a schema for this.

4.  **Implement the service handler:**
    The service handler function (e.g., `async_handle_get_minute_forecast`) will:
    *   Retrieve the `config_entry` using the `entity_id` (via `EntityRegistry`) or the provided `config_entry_id`.
    *   Check if the entry exists and if its state is `ConfigEntryState.LOADED`.
    *   If not, raise `ServiceValidationError` with a clear message (as per the rule's example).
    *   Access necessary data (like `coordinator` and `mode`) from `entry.runtime_data`.
    *   Execute the original service logic to fetch and return the minute forecast.

5.  **Update `services.yaml`:**
    Modify `homeassistant/components/openweathermap/services.yaml` to reflect that `get_minute_forecast` is now a domain service, including its new fields (e.g., `entity_id`).

**Example Code Snippets:**

**In `homeassistant/components/openweathermap/__init__.py`:**
```python
from __future__ import annotations

from dataclasses import dataclass
import logging

from pyopenweathermap import create_owm_client
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_MODE,
    CONF_NAME,
    ATTR_ENTITY_ID, # Add this
)
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, ConfigType # Add ServiceCall, SupportsResponse, ConfigType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er # Add cv, er

from .const import (
    CONFIG_FLOW_VERSION,
    DEFAULT_OWM_MODE,
    DOMAIN, # Add DOMAIN
    OWM_MODES,
    PLATFORMS,
    SERVICE_GET_MINUTE_FORECAST, # Assuming this is defined in const.py
    ATTR_API_MINUTE_FORECAST, # Add this
    OWM_MODE_V30, # Add this
    DEFAULT_NAME, # Add this
)
from .coordinator import WeatherUpdateCoordinator
from .repairs import async_create_issue, async_delete_issue
from .utils import build_data_and_options

_LOGGER = logging.getLogger(__name__)

type OpenweathermapConfigEntry = ConfigEntry[OpenweathermapData]


@dataclass
class OpenweathermapData:
    """Runtime data definition."""

    name: str
    mode: str
    coordinator: WeatherUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up OpenWeatherMap integration and register services."""

    async def async_handle_get_minute_forecast(call: ServiceCall) -> dict | None:
        """Handle the get_minute_forecast service call."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        ent_reg = er.async_get(hass)

        if not entity_id or not (entity_entry := ent_reg.async_get(entity_id)):
            raise ServiceValidationError(f"Entity {entity_id} not found.")

        if entity_entry.platform != DOMAIN or entity_entry.domain != "weather":
            raise ServiceValidationError(f"Entity {entity_id} is not an OpenWeatherMap weather entity.")

        config_entry_id = entity_entry.config_entry_id
        entry = hass.config_entries.async_get_entry(config_entry_id)

        if not entry:
            # This case should ideally not happen if entity_entry exists
            raise ServiceValidationError(
                f"Configuration entry for {entity_id} not found."
            )

        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                f"Configuration entry '{entry.title}' for entity {entity_id} is not loaded (current state: {entry.state})."
            )

        # Access runtime_data which should be OpenweathermapData
        if not isinstance(entry.runtime_data, OpenweathermapData):
            raise ServiceValidationError(
                f"Integration data for '{entry.title}' (entity {entity_id}) is not ready."
            )
        
        owm_data: OpenweathermapData = entry.runtime_data
        weather_coordinator = owm_data.coordinator
        mode = owm_data.mode

        if mode == OWM_MODE_V30:
            if not weather_coordinator.data or ATTR_API_MINUTE_FORECAST not in weather_coordinator.data:
                # Could also trigger a refresh here if appropriate and wait, or ensure data is fresh
                raise ServiceValidationError(
                    f"Minute forecast data not available for '{entry.title}' (entity {entity_id}). Coordinator may need to refresh."
                )
            return weather_coordinator.data[ATTR_API_MINUTE_FORECAST]
        
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="exceptions.service_minute_forecast_mode", # ensure this key exists in strings.json
            translation_placeholders={"name": entry.title or DEFAULT_NAME},
        )

    SERVICE_GET_MINUTE_FORECAST_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        }
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_MINUTE_FORECAST, # This should be "get_minute_forecast"
        async_handle_get_minute_forecast,
        schema=SERVICE_GET_MINUTE_FORECAST_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    return True # Essential for async_setup to indicate success

# ... (async_setup_entry, async_migrate_entry, etc. remain)
```

**In `homeassistant/components/openweathermap/const.py` (ensure these exist):**
```python
# ...
SERVICE_GET_MINUTE_FORECAST = "get_minute_forecast"
# ...
```

**In `homeassistant/components/openweathermap/services.yaml`:**
```yaml
get_minute_forecast:
  name: Get minute forecast
  description: Retrieves a minute-by-minute weather forecast for one hour for the targeted OpenWeatherMap weather entity.
  target: # Keep target for service call UI if desired, but main logic uses entity_id from fields
    entity:
      integration: openweathermap
      domain: weather
  fields:
    entity_id:
      name: Entity
      description: The OpenWeatherMap weather entity to get the forecast for.
      required: true
      example: "weather.openweathermap_location_name"
      selector:
        entity:
          integration: openweathermap
          domain: weather
```
*Note: The `target` field in `services.yaml` for a domain service usually defines how the UI presents targeting options. The actual `entity_id` passed to the service handler comes from the `fields` data.*

**Remove service registration from `homeassistant/components/openweathermap/weather.py`:**
Delete the `platform.async_register_entity_service(...)` call from `weather.py::async_setup_entry`.

These changes would ensure the `get_minute_forecast` service is always defined at the domain level. The service call itself would then correctly validate if the targeted entity and its underlying config entry are loaded and ready, providing specific error messages as intended by the rule.

_Created at 2025-05-14 15:11:52. Prompt tokens: 13933, Output tokens: 2507, Total tokens: 22302_
