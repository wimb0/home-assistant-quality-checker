# adax: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **done**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `appropriate-polling` rule applies to this integration because `adax` is a polling integration. This is indicated by its `iot_class` being `"local_polling"` in the `manifest.json` file, and its use of the `DataUpdateCoordinator` to periodically fetch data.

The integration correctly follows this rule. It establishes a polling interval for both its cloud and local connection modes.

In `homeassistant/components/adax/coordinator.py`, both `AdaxCloudCoordinator` and `AdaxLocalCoordinator` classes set the `update_interval` parameter in their `super().__init__` calls:

```python
# homeassistant/components/adax/coordinator.py
class AdaxCloudCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator for updating data to and from Adax (cloud)."""

    def __init__(self, hass: HomeAssistant, entry: AdaxConfigEntry) -> None:
        """Initialize the Adax coordinator used for Cloud mode."""
        super().__init__(
            hass,
            config_entry=entry,
            logger=_LOGGER,
            name="AdaxCloud",
            update_interval=SCAN_INTERVAL,  # Polling interval set here
        )
        # ...

class AdaxLocalCoordinator(DataUpdateCoordinator[dict[str, Any] | None]):
    """Coordinator for updating data to and from Adax (local)."""

    def __init__(self, hass: HomeAssistant, entry: AdaxConfigEntry) -> None:
        """Initialize the Adax coordinator used for Local mode."""
        super().__init__(
            hass,
            config_entry=entry,
            logger=_LOGGER,
            name="AdaxLocal",
            update_interval=SCAN_INTERVAL,  # Polling interval set here
        )
        # ...
```

The `SCAN_INTERVAL` is defined in `homeassistant/components/adax/const.py`:
```python
# homeassistant/components/adax/const.py
SCAN_INTERVAL = datetime.timedelta(seconds=60)
```
This sets the polling interval to 60 seconds (1 minute). For climate devices like Adax heaters, a 60-second polling interval is generally considered appropriate. It provides a reasonable balance between responsiveness to state changes (e.g., temperature changes, manual adjustments on the device) and efficient use of resources (network, API calls). This interval should serve the majority of users well, and those who require different polling frequencies can customize it as per Home Assistant's common tasks.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:02:31. Prompt tokens: 6813, Output tokens: 698, Total tokens: 8901_
