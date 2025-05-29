# jewish_calendar: diagnostics

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [diagnostics](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `diagnostics` rule requires integrations that use config entries to implement a diagnostics platform to help users debug issues. This involves creating a `diagnostics.py` file with an `async_get_config_entry_diagnostics` function and ensuring sensitive information is redacted.

The `jewish_calendar` integration **applies** to this rule as it has `config_flow: true` in its `manifest.json`, indicating it uses config entries.

The integration currently does **NOT fully follow** the rule.
While a `diagnostics.py` file exists and implements the `async_get_config_entry_diagnostics` function with redaction for sensitive data like latitude, longitude, and altitude, the integration's `manifest.json` file is missing the necessary `"diagnostics": ["config_entry"]` entry. This entry is required for Home Assistant to discover and use the provided diagnostics platform.

**Code Analysis:**

1.  **`diagnostics.py` Implementation:**
    The file `homeassistant/components/jewish_calendar/diagnostics.py` is present:
    ```python
    # homeassistant/components/jewish_calendar/diagnostics.py
    TO_REDACT = [
        CONF_ALTITUDE,  # "altitude"
        CONF_LATITUDE,  # "latitude"
        CONF_LONGITUDE, # "longitude"
    ]

    async def async_get_config_entry_diagnostics(
        hass: HomeAssistant, entry: JewishCalendarConfigEntry
    ) -> dict[str, Any]:
        """Return diagnostics for a config entry."""

        return {
            "entry_data": async_redact_data(entry.data, TO_REDACT),
            "data": async_redact_data(asdict(entry.runtime_data), TO_REDACT),
        }
    ```
    This implementation correctly:
    *   Defines the `async_get_config_entry_diagnostics` function.
    *   Includes `entry.data` and `entry.runtime_data`.
    *   Uses `async_redact_data` to redact sensitive information. The `TO_REDACT` list includes `CONF_LATITUDE`, `CONF_LONGITUDE`, and `CONF_ALTITUDE` (which is defined as `"altitude"` in `jewish_calendar/const.py` and corresponds to `CONF_ELEVATION` from Home Assistant's core config). This correctly covers sensitive location data in both `entry.data` and `entry.runtime_data` (specifically within the `location` object).

2.  **`manifest.json` Configuration:**
    The `homeassistant/components/jewish_calendar/manifest.json` file is:
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
    This file is missing the `"diagnostics": ["config_entry"]` line. Without this, the diagnostics functionality, although coded, will not be available to users through the Home Assistant UI or system.

Because the `manifest.json` does not declare the diagnostics platform, the integration does not fully meet the requirements of the rule.

## Suggestions

To make the `jewish_calendar` integration compliant with the `diagnostics` rule, the following change is necessary:

1.  **Update `manifest.json`:**
    Add the `diagnostics` key to the `homeassistant/components/jewish_calendar/manifest.json` file.

    **Current `manifest.json`:**
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

    **Modified `manifest.json`:**
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
      "single_config_entry": true,
      "diagnostics": ["config_entry"]  <-- Add this line
    }
    ```

    **Reasoning:**
    Adding `"diagnostics": ["config_entry"]` to the `manifest.json` registers the diagnostics platform with Home Assistant, allowing users to download diagnostics data for config entries of this integration. This makes the implemented `diagnostics.py` functional within the Home Assistant ecosystem.

_Created at 2025-05-29 08:22:10. Prompt tokens: 13286, Output tokens: 1334, Total tokens: 17668_
