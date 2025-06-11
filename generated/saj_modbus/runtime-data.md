# saj_modbus: runtime-data
| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **todo**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `runtime-data` rule applies to this integration because it creates and manages a `SAJModbusHub` object at runtime. This hub instance is responsible for device communication and data coordination, which is precisely the type of data that should be stored as runtime data.

The integration currently does **not** follow this rule. Instead of using the recommended `ConfigEntry.runtime_data` attribute, it stores the `SAJModbusHub` instance in the global `hass.data` dictionary.

This is evident in `__init__.py`:

```python
# homeassistant/components/saj_modbus/__init__.py:61-64
hub = SAJModbusHub(hass, name, host, port, scan_interval)
await hub.async_config_entry_first_refresh()

"""Register the hub."""
hass.data[DOMAIN][name] = {"hub": hub}
```

This legacy pattern makes accessing the runtime object more cumbersome and less explicit than the modern `entry.runtime_data` approach. Other parts of the integration, such as the platform setup files (`sensor.py`, `number.py`) and the service handler (`services.py`), then retrieve the hub from `hass.data`, confirming the anti-pattern.

To comply with the rule, the integration should store the `SAJModbusHub` instance on `entry.runtime_data` and update all access points to retrieve it from there.

## Suggestions

To make the `saj_modbus` integration compliant, you should refactor the code to use `ConfigEntry.runtime_data` to store the `SAJModbusHub` instance.

### 1. Update `__init__.py`

Modify `async_setup_entry` to store the hub in `entry.runtime_data` and clean up the `hass.data` usage. It is also a best practice to create a typed `ConfigEntry`.

```python
# homeassistant/components/saj_modbus/__init__.py

import asyncio
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .hub import SAJModbusHub
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

# Define a typed ConfigEntry for better type hinting
type SajModbusConfigEntry = ConfigEntry[SAJModbusHub]

# ... (SAJ_MODBUS_SCHEMA and CONFIG_SCHEMA remain the same) ...

PLATFORMS = ["sensor", "number"]


async def async_setup(hass, config):
    """Set up the SAJ modbus component."""
    # This can now be removed if not used for other purposes
    # hass.data[DOMAIN] = {} 
    return True

async def async_setup_entry(hass: HomeAssistant, entry: SajModbusConfigEntry):
    """Set up a SAJ mobus."""
    # Remove: hass.data.setdefault(DOMAIN, {})

    host = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    port = entry.data.get(CONF_PORT)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    _LOGGER.debug("Setup %s.%s", DOMAIN, name)

    hub = SAJModbusHub(hass, name, host, port, scan_interval)
    await hub.async_config_entry_first_refresh()

    # --- CHANGE HERE ---
    # Store the hub instance in runtime_data instead of hass.data
    entry.runtime_data = hub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload SAJ modbus entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    # --- CHANGE HERE ---
    # The pop from hass.data is no longer needed, as runtime_data is managed
    # automatically with the lifecycle of the config entry.
    # hass.data[DOMAIN].pop(entry.data["name"])

    return True

# ... (rest of the file) ...
```

### 2. Update Platform Setup (`sensor.py` and `number.py`)

In `sensor.py` and `number.py`, retrieve the `hub` instance directly from `entry.runtime_data`.

**Example for `sensor.py`:**
```python
# homeassistant/components/saj_modbus/sensor.py

# ... (imports) ...
# Import the new typed ConfigEntry
from . import SajModbusConfigEntry
from .hub import SAJModbusHub

# ...

async def async_setup_entry(hass, entry: SajModbusConfigEntry, async_add_entities):
    """Set up entry for hub."""
    # --- CHANGE HERE ---
    # hub_name = entry.data[CONF_NAME]  <- No longer needed to get the hub
    # hub = hass.data[DOMAIN][hub_name]["hub"] <- OLD WAY
    hub = entry.runtime_data # NEW WAY

    device_info = {
        "identifiers": {(DOMAIN, entry.data[CONF_NAME])},
        "name": entry.data[CONF_NAME],
        "manufacturer": ATTR_MANUFACTURER,
    }

    # ... (rest of the function is unchanged) ...
```
The same change should be applied to `number.py`.

### 3. Update `services.py`

The service call needs to find the correct `ConfigEntry` associated with the `device_id` to access its `runtime_data`.

```python
# homeassistant/components/saj_modbus/services.py

# ... (imports) ...
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry as dr, config_validation as cv

# ... (schemas and constants) ...

async def async_set_date_time(hass: HomeAssistant, data: Mapping[str, Any]) -> None:
    """Set the date and time on the inverter."""
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(data[ATTR_DEVICE_ID])

    if not device_entry or not device_entry.config_entries:
        # It's good practice to log an error here
        return

    # Find the config entry associated with this device
    config_entry_id = next(iter(device_entry.config_entries))
    config_entry = hass.config_entries.async_get_entry(config_entry_id)

    if not config_entry or not hasattr(config_entry, "runtime_data"):
        # It's good practice to log an error here
        return
    
    # --- CHANGE HERE ---
    # OLD WAY: hub = hass.data[SAJ_DOMAIN][device_entry.name]["hub"]
    hub = config_entry.runtime_data

    await hass.async_add_executor_job(
        hub.set_date_and_time, data.get(ATTR_DATETIME, None)
    )
```

---

_Created at 2025-06-11 21:34:32. Prompt tokens: 16629, Output tokens: 1888, Total tokens: 22518._

_AI can be wrong. Always verify the report and the code against the rule._
