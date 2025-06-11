# saj_modbus: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **todo**                                                                 |

## Overview

The `action-setup` rule requires that integration-provided services are registered in the `async_setup` function, not `async_setup_entry`. This ensures that services are always available for validation, even if the configuration entry is not loaded.

The `saj_modbus` integration provides a `set_datetime` service but does not follow this rule.

1.  **Service Registration Location:** In `homeassistant/components/saj_modbus/__init__.py`, the service registration is initiated within `async_setup_entry`:

    ```python
    # homeassistant/components/saj_modbus/__init__.py:78
    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
        # ...
        async_setup_services(hass)
        return True
    ```

    This call should be moved to the `async_setup` function. Because it's in `async_setup_entry`, the service will only be available after a config entry has been successfully loaded.

2.  **Service Handler Implementation:** The service handler in `homeassistant/components/saj_modbus/services.py` does not validate whether the targeted config entry is loaded.

    ```python
    # homeassistant/components/saj_modbus/services.py:53
    async def async_set_date_time(hass: HomeAssistant, data: Mapping[str, Any]) -> None:
        """Set the date and time on the inverter."""
        device_registry = dr.async_get(hass)
        device_entry = device_registry.async_get(data[ATTR_DEVICE_ID])

        hub = hass.data[SAJ_DOMAIN][device_entry.name]["hub"]
        # ...
    ```

    If this service is called when the corresponding config entry is not loaded (e.g., the inverter is offline at startup), the line `hub = hass.data[SAJ_DOMAIN][device_entry.name]["hub"]` will raise a `KeyError` because the `hub` object is only added to `hass.data` during `async_setup_entry`. The service call will fail with an unhandled exception instead of raising a user-friendly `ServiceValidationError`.

To comply with the rule, the registration must be moved to `async_setup`, and the service handler must be updated to check the state of the config entry before attempting to act on it.

## Suggestions

To make the `saj_modbus` integration compliant, you need to modify the service registration logic and the service handler.

**1. Move Service Registration to `async_setup`**

In `homeassistant/components/saj_modbus/__init__.py`, move the call to `async_setup_services` from `async_setup_entry` to `async_setup`.

```python
# homeassistant/components/saj_modbus/__init__.py

# ... (imports)

async def async_setup(hass, config):
    """Set up the SAJ modbus component."""
    hass.data[DOMAIN] = {}
    async_setup_services(hass)  # <-- Add this line
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up a SAJ mobus."""
    # ... (rest of the function)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # async_setup_services(hass) <-- Remove this line

    return True

# ...
```

**2. Refactor the Service Handler**

In `homeassistant/components/saj_modbus/services.py`, refactor the service registration and handler to validate the config entry state. This involves checking if the entry is loaded and raising a `ServiceValidationError` if it is not.

It is also recommended to register the service handler directly instead of using a dispatcher function (`async_call_service`).

Here is the suggested new content for `homeassistant/components/saj_modbus/services.py`:

```python
"""SAJ Modbus services."""

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_DEVICE_ID, CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import DOMAIN as SAJ_DOMAIN

ATTR_DATETIME = "datetime"

SERVICE_SET_DATE_TIME = "set_datetime"

SERVICE_SET_DATE_TIME_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(ATTR_DEVICE_ID): str,
            vol.Optional(ATTR_DATETIME): cv.datetime,
        }
    )
)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for SAJ Modbus integration."""

    async def async_set_date_time(call: ServiceCall) -> None:
        """Service handler to set the date and time on the inverter."""
        device_registry = dr.async_get(hass)
        device_entry = device_registry.async_get(call.data[ATTR_DEVICE_ID])

        if not device_entry:
            raise ServiceValidationError(f"Device with ID {call.data[ATTR_DEVICE_ID]} not found.")

        # Find the config entry associated with this device for this integration
        config_entry_id = None
        for entry_id in device_entry.config_entries:
            if (entry := hass.config_entries.async_get_entry(entry_id)) and entry.domain == SAJ_DOMAIN:
                config_entry_id = entry.entry_id
                break

        if not config_entry_id:
            raise ServiceValidationError(f"No {SAJ_DOMAIN} config entry found for device {call.data[ATTR_DEVICE_ID]}.")

        entry = hass.config_entries.async_get_entry(config_entry_id)
        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(f"Config entry for device {call.data[ATTR_DEVICE_ID]} is not loaded.")

        # Use the name from the config entry data for a more robust lookup
        hub_name = entry.data[CONF_NAME]
        hub = hass.data[SAJ_DOMAIN][hub_name]["hub"]
        await hass.async_add_executor_job(
            hub.set_date_and_time, call.data.get(ATTR_DATETIME)
        )

    hass.services.async_register(
        SAJ_DOMAIN,
        SERVICE_SET_DATE_TIME,
        async_set_date_time,
        schema=SERVICE_SET_DATE_TIME_SCHEMA,
    )


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Unload SAJ Modbus services."""
    # Services registered in async_setup are not typically removed.
    # This function can be removed if no longer used.
    hass.services.async_remove(SAJ_DOMAIN, SERVICE_SET_DATE_TIME)

```

**Why these changes help:**

*   By moving the registration to `async_setup`, the `set_datetime` service will be registered when Home Assistant starts, allowing UI elements and automations to be validated correctly.
*   The updated `async_set_date_time` handler now finds the associated config entry and checks its `state`. If the entry isn't `LOADED`, it raises a `ServiceValidationError`, which provides clear feedback to the user instead of causing an unhandled error.
*   The logic to find the `hub` is made more robust by using `entry.data[CONF_NAME]` instead of `device_entry.name`, as the device name can be changed by the user.
*   The `async_unload_services` function is generally not needed for services registered in `async_setup`. You can likely remove it and its call from `async_unload_entry` (if it existed) for cleaner code.

---

_Created at 2025-06-11 21:29:56. Prompt tokens: 16787, Output tokens: 1972, Total tokens: 22757._

_AI can be wrong. Always verify the report and the code against the rule._
