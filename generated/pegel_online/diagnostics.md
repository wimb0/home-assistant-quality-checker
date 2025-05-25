```markdown
# pegel_online: diagnostics

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [diagnostics](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires integrations to implement diagnostics to help users and developers debug issues. It also mandates that sensitive information, such as coordinates, should not be exposed in the diagnostics output.

The `pegel_online` integration has implemented the diagnostics feature by including a `diagnostics.py` file with the `async_get_config_entry_diagnostics` function. This function returns the configuration entry data and the current coordinator data, which fulfills the basic requirement of providing diagnostic information.

However, the implementation in `homeassistant/components/pegel_online/diagnostics.py` directly includes `entry.as_dict()`, which contains the configuration data (`entry.data`). The configuration data for this integration, as seen in `homeassistant/components/pegel_online/config_flow.py`, includes the user's selected location with `CONF_LATITUDE` and `CONF_LONGITUDE`. Exposing these coordinates directly in the diagnostics output violates the rule's requirement to not expose sensitive information like coordinates.

Therefore, while diagnostics are implemented, the integration does not fully follow the rule because it includes sensitive location data without redaction.

## Suggestions

To comply with the diagnostics rule regarding sensitive data, the integration should redact the latitude and longitude from the configuration entry data before including it in the diagnostics output.

Here are the steps to modify `homeassistant/components/pegel_online/diagnostics.py`:

1.  Import the necessary constants (`CONF_LATITUDE`, `CONF_LONGITUDE`) and the `async_redact_data` helper.
2.  Define a list `TO_REDACT` containing the keys for latitude and longitude.
3.  Apply `async_redact_data` to the config entry data before adding it to the diagnostics dictionary.

```python
"""Diagnostics support for pegel_online."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE # Import constants
from homeassistant.core import HomeAssistant

from .coordinator import PegelOnlineConfigEntry
from .const import CONF_LOCATION # Import constant for clarity

TO_REDACT = [
    f"{CONF_LOCATION}.{CONF_LATITUDE}", # Use dot notation for nested keys
    f"{CONF_LOCATION}.{CONF_LONGITUDE}",
]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PegelOnlineConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT), # Redact sensitive data
        "data": coordinator.data,
    }

```

By implementing these changes, the latitude and longitude stored in the configuration entry will be redacted (replaced with `**REDACTED**`) in the diagnostics output, bringing the integration into full compliance with the rule.
```

_Created at 2025-05-25 11:24:13. Prompt tokens: 5715, Output tokens: 780, Total tokens: 7584_
