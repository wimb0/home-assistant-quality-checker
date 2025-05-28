# overkiz: diagnostics

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [diagnostics](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `diagnostics` rule requires integrations to provide a way for users to download diagnostic information, which should be free of sensitive data like passwords, tokens, or coordinates.

The `overkiz` integration implements a `diagnostics.py` file with both `async_get_config_entry_diagnostics` and `async_get_device_diagnostics` functions. This is a good foundation.

However, the integration does not fully meet the rule's requirements for the following reasons:

1.  **Incomplete Redaction of Library Data:** The diagnostic functions retrieve a significant amount of data via `client.get_diagnostic_data()` from the `pyoverkiz` library. While `pyoverkiz` performs some redaction (e.g., for common credential keys like "password", "token"), it may not redact all types of sensitive information as per Home Assistant guidelines. Specifically, if Overkiz devices report coordinates (e.g., via states like `core:LatitudeState` or `core:LongitudeState`), the `pyoverkiz` library's default redaction mechanism (checked against `pyoverkiz.obfuscate.REDACT_KEYS` and `REDACT_SUBSTRINGS`) is unlikely to catch these. The `overkiz` integration currently passes this data through without applying further redaction using Home Assistant's `async_redact_data` helper for such cases. This could lead to the exposure of coordinates.

2.  **Omission of Redacted `entry.data`:** The rule's example implementation shows the inclusion of `entry.data` after redacting sensitive fields. The `overkiz` integration's `entry.data` contains sensitive information such as `CONF_USERNAME`, `CONF_PASSWORD` (for cloud API), and `CONF_TOKEN` (for local API). The current diagnostic implementation avoids leaking these specific credentials by *omitting* `entry.data` entirely from the output, rather than including a redacted version. While this prevents direct leakage from `entry.data`, it deviates from the common practice shown in the rule's example and means that potentially useful non-sensitive configuration options (e.g., `CONF_VERIFY_SSL`, `CONF_HOST` if not otherwise included and obfuscated) are not available in the diagnostics.

The `overkiz/diagnostics.py` file:
```python
# homeassistant/components/overkiz/diagnostics.py
# ...
async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: OverkizDataConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    client = entry.runtime_data.coordinator.client

    data = {
        "setup": await client.get_diagnostic_data(), # Relies on pyoverkiz for redaction
        "server": entry.data[CONF_HUB],
        "api_type": entry.data.get(CONF_API_TYPE, APIType.CLOUD),
    }
    # ...
    return data

async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: OverkizDataConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    client = entry.runtime_data.coordinator.client
    # ...
    data = {
        "device": {
            # ...
            "device_url": obfuscate_id(device_url), # Good
        },
        "setup": await client.get_diagnostic_data(), # Relies on pyoverkiz for redaction
        "server": entry.data[CONF_HUB],
        "api_type": entry.data.get(CONF_API_TYPE, APIType.CLOUD),
    }
    # ...
    return data
```
This code does not use `async_redact_data` from `homeassistant.helpers.redact` for the `setup` data nor does it include a redacted version of `entry.data`.

## Suggestions

To make the `overkiz` integration compliant with the `diagnostics` rule:

1.  **Include and Redact `entry.data`:**
    Modify `async_get_config_entry_diagnostics` (and `async_get_device_diagnostics` if `entry.data` is relevant there) to include a redacted version of the config entry's data. This makes non-sensitive configuration available for debugging while protecting sensitive details.

    Update `homeassistant/components/overkiz/diagnostics.py`:
    ```python
    from homeassistant.const import (
        CONF_HOST, # If considered sensitive, especially if it can be an IP
        CONF_PASSWORD,
        CONF_TOKEN,
        CONF_USERNAME,
    )
    from homeassistant.helpers.redact import async_redact_data
    # ... other imports from overkiz ...

    # Define sensitive keys from entry.data
    TO_REDACT_CONFIG = [CONF_USERNAME, CONF_PASSWORD, CONF_TOKEN, CONF_HOST]
    # Define potential sensitive keys that might appear in pyoverkiz data (especially coordinates)
    # This list would need to be based on known states/attributes from pyoverkiz that could be sensitive
    # e.g. "core:LatitudeState", "core:LongitudeState", "latitude", "longitude"
    TO_REDACT_SETUP_DATA = ["latitude", "longitude"] # Add more as identified

    async def async_get_config_entry_diagnostics(
        hass: HomeAssistant, entry: OverkizDataConfigEntry
    ) -> dict[str, Any]:
        """Return diagnostics for a config entry."""
        client = entry.runtime_data.coordinator.client

        raw_setup_data = await client.get_diagnostic_data()
        
        data = {
            "entry": async_redact_data(entry.data, TO_REDACT_CONFIG),
            "setup": async_redact_data(raw_setup_data, TO_REDACT_SETUP_DATA), # Apply redaction to library output
            # server and api_type are already part of entry.data, so they will be included via the above
        }

        if client.api_type == APIType.CLOUD:
            execution_history = [
                repr(execution) for execution in await client.get_execution_history()
            ]
            # Execution history should also be checked for sensitive data or redacted if necessary
            data["execution_history"] = async_redact_data(execution_history, TO_REDACT_SETUP_DATA)


        return data

    async def async_get_device_diagnostics(
        hass: HomeAssistant, entry: OverkizDataConfigEntry, device: DeviceEntry
    ) -> dict[str, Any]:
        """Return diagnostics for a device entry."""
        client = entry.runtime_data.coordinator.client
        device_url = min(device.identifiers)[1]
        
        raw_setup_data = await client.get_diagnostic_data()

        data = {
            "entry": async_redact_data(entry.data, TO_REDACT_CONFIG), # Include redacted entry data
            "device_info": { # Renamed 'device' to avoid conflict if 'device' is a key in raw_setup_data
                "controllable_name": device.hw_version,
                "firmware": device.sw_version,
                "device_url": obfuscate_id(device_url),
                "model": device.model,
            },
            "setup": async_redact_data(raw_setup_data, TO_REDACT_SETUP_DATA),
        }

        if client.api_type == APIType.CLOUD:
            # Filter execution history for the specific device
            device_execution_history = [
                repr(execution)
                for execution in await client.get_execution_history()
                if any(command.device_url == device_url for command in execution.commands)
            ]
            data["execution_history"] = async_redact_data(device_execution_history, TO_REDACT_SETUP_DATA)

        return data
    ```

2.  **Ensure Comprehensive Redaction of Library Data (`setup` key):**
    The `TO_REDACT_SETUP_DATA` list in the example above is illustrative. A thorough review of the data structures returned by `pyoverkiz.client.get_diagnostic_data()` and `pyoverkiz.client.get_execution_history()` is needed to identify all potentially sensitive keys, especially those related to location/coordinates (e.g., `latitude`, `longitude`, `core:LatitudeState`, `gpsPosition`, etc.), and add them to `TO_REDACT_SETUP_DATA`. Using `async_redact_data` on this data ensures that the integration takes responsibility for redacting according to Home Assistant standards, even if the underlying library's redaction is not exhaustive for all HA-defined sensitive types.

    *Why these changes satisfy the rule:*
    *   Including redacted `entry.data` aligns with the rule's example, provides more comprehensive (yet safe) configuration information for debugging, and ensures non-sensitive config options like `CONF_VERIFY_SSL` are available.
    *   Applying `async_redact_data` to the data from `pyoverkiz` (under the `"setup"` key and `"execution_history"`) ensures that the integration actively redacts potentially sensitive information like coordinates, fulfilling the requirement that "diagnostics should not expose any sensitive information." This makes the redaction more robust and less solely dependent on the library's specific redaction keys.

_Created at 2025-05-28 12:27:27. Prompt tokens: 86819, Output tokens: 2286, Total tokens: 97050_
