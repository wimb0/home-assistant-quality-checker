# open_epaper_link: diagnostics

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [diagnostics](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics)                                                     |
| Status | **todo**                                       |

## Overview

The `diagnostics` rule applies to the `open_epaper_link` integration. This rule encourages providing a way for users to download diagnostic information, which is crucial for debugging and troubleshooting. Integrations that manage devices or services, especially hub-based ones like `open_epaper_link`, benefit significantly from diagnostics as they often maintain complex runtime states. The `open_epaper_link` integration uses a config entry (as seen by `config_flow.py` and `manifest.json` specifying `config_flow: true`) and manages a `Hub` instance (in `hub.py`) which holds runtime data about the access point (AP) and connected E-Paper tags.

Currently, the `open_epaper_link` integration does **NOT** follow this rule.
There is no `diagnostics.py` file within the `homeassistant/components/open_epaper_link/` directory, and consequently, the required `async_get_config_entry_diagnostics` function is not implemented. This means users cannot easily export a snapshot of the integration's configuration and state for support purposes.

## Suggestions

To make the `open_epaper_link` integration compliant with the `diagnostics` rule, the following steps should be taken:

1.  **Create `diagnostics.py`:**
    Add a new file named `diagnostics.py` in the `homeassistant/components/open_epaper_link/` directory.

2.  **Implement `async_get_config_entry_diagnostics`:**
    Inside `diagnostics.py`, implement the `async_get_config_entry_diagnostics` function. This function should gather relevant information from the config entry and the `Hub` instance.

3.  **Identify and Redact Sensitive Information:**
    The diagnostics data should not expose sensitive user information. For `open_epaper_link`, consider redacting:
    *   `custom_font_dirs` from `entry.options` if it can reveal full file paths.
    *   `wifi_ssid` from the AP status (part of `hub.ap_status`).
    Use `homeassistant.components.diagnostics.async_redact_data` for redaction.

4.  **Include Relevant Data:**
    The diagnostics should include:
    *   Config entry details (data and options, redacted).
    *   Hub status and configuration (`hub.online`, `hub.ap_model`, `hub.ap_env`, `hub.ap_status`, `hub.ap_config`).
    *   Information about known and blacklisted tags (e.g., counts, MAC addresses).
    *   Integration version from the manifest.

**Example `diagnostics.py`:**

```python
# homeassistant/components/open_epaper_link/diagnostics.py
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
# from homeassistant.const import CONF_HOST # CONF_HOST is usually not sensitive for local IPs
from homeassistant.core import HomeAssistant

from .const import DOMAIN
# If you add CONF_CUSTOM_FONT_DIRS to const.py, import it:
# from .const import CONF_CUSTOM_FONT_DIRS
from .hub import Hub

# Keys to redact from config entry options
# If CONF_CUSTOM_FONT_DIRS were a defined constant:
# TO_REDACT_OPTIONS_DATA = {
#     CONF_CUSTOM_FONT_DIRS,
# }
# Using string literal as per current codebase:
TO_REDACT_OPTIONS_DATA = {
    "custom_font_dirs",
}

# Keys to redact from AP status data
TO_REDACT_AP_STATUS_DATA = {
    "wifi_ssid",
}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    hub: Hub = hass.data[DOMAIN][entry.entry_id]

    # Get integration manifest
    manifest = await hass.loader.async_get_integration(DOMAIN)

    diagnostics_data = {
        "manifest_version": str(manifest.version) if manifest else "Unknown",
        "config_entry": {
            "title": entry.title,
            "entry_id": entry.entry_id,
            "data": async_redact_data(dict(entry.data), {}), # Typically CONF_HOST, not redacted
            "options": async_redact_data(dict(entry.options), TO_REDACT_OPTIONS_DATA),
            "source": entry.source,
            "version": entry.version,
            "disabled_by": entry.disabled_by,
        },
        "hub_data": {
            "online": hub.online,
            "host": hub.host,
            "ap_model": hub.ap_model,
            "ap_env": hub.ap_env,
            "ap_status": async_redact_data(hub.ap_status, TO_REDACT_AP_STATUS_DATA),
            "ap_config": hub.ap_config,  # Review if hub.ap_config contains sensitive data
            "known_tags_summary": {
                "count": len(hub.tags),
                "macs": hub.tags,
            },
            "blacklisted_tags_summary": {
                "count": len(hub.get_blacklisted_tags()),
                "macs": hub.get_blacklisted_tags(),
            },
        },
    }
    return diagnostics_data

```

**Explanation of Changes:**

*   The `diagnostics.py` file provides the `async_get_config_entry_diagnostics` hook required by Home Assistant.
*   It gathers data from both the `ConfigEntry` (like `host`, `custom_font_dirs`) and the `Hub` (like AP status, AP config, tag lists).
*   `async_redact_data` is used to hide potentially sensitive information like `custom_font_dirs` (if it's an absolute path) and `wifi_ssid`.
*   This provides valuable debugging information to users and developers without compromising sensitive data, fulfilling the requirements of the `diagnostics` rule.

**To complete this, consider:**
*   Adding `CONF_CUSTOM_FONT_DIRS = "custom_font_dirs"` to your `const.py` for cleaner code, then import and use it in `diagnostics.py`.
*   Thoroughly reviewing `hub.ap_config` to ensure no sensitive values are present, or add them to a redaction list if necessary.

_Created at 2025-05-14 20:56:25. Prompt tokens: 60308, Output tokens: 1626, Total tokens: 67272_
