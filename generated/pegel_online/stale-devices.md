```markdown
# pegel_online: stale-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [stale-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/stale-devices)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `stale-devices` rule requires integrations to remove devices from the Home Assistant device registry when they are no longer available from the source, or at least allow manual removal via `async_remove_config_entry_device`.

This rule applies to the `pegel_online` integration because it registers devices in Home Assistant. As seen in `homeassistant/components/pegel_online/entity.py`, a `DeviceInfo` is created for each configured station with identifiers based on the station's UUID:

```python
self._attr_device_info = DeviceInfo(
    identifiers={(DOMAIN, self.station.uuid)},
    name=f"{self.station.name} {self.station.water_name}",
    manufacturer=self.station.agency,
    configuration_url=self.station.base_data_url,
    entry_type=DeviceEntryType.SERVICE,
)
```

The pegel_online integration config flow sets up *one* station per config entry. The API (`aiopegelonline`) fetches data for a specific station or searches for nearby stations, but it does not provide a list of *all* stations associated with a hypothetical "account" or "hub" instance. Therefore, the integration architecture (one config entry per station) does not lend itself to automatically detecting "removed" stations by comparing a list of currently available stations from the API with a previously known list (as shown in the first example of the rule).

However, the rule also allows implementing `async_remove_config_entry_device` in `__init__.py` to permit users to manually remove device entries from the UI if automatic removal isn't feasible or reliable. Reviewing `homeassistant/components/pegel_online/__init__.py`, this function is not implemented.

Because the integration creates device entries but does not implement `async_remove_config_entry_device` to allow manual removal of potentially stale devices (e.g., if a station permanently stops reporting or is removed from the API), it does not fully comply with the `stale-devices` rule.

## Suggestions

To comply with the `stale-devices` rule, the `pegel_online` integration should implement the `async_remove_config_entry_device` function in `homeassistant/components/pegel_online/__init__.py`.

This function should return `True` to indicate that Home Assistant is allowed to remove the device associated with the config entry. Since the integration manages only one "device" (station) per config entry, allowing removal of the device is appropriate when the user chooses to remove it via the UI, as the associated config entry would likely also be removed or already gone.

Add the following function to `homeassistant/components/pegel_online/__init__.py`:

```python
# In homeassistant/components/pegel_online/__init__.py

# ... existing imports and code ...

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: PegelOnlineConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    # In this integration, each config entry corresponds to exactly one device (station).
    # We can allow removal of the device via the UI, which typically happens
    # in conjunction with removing the config entry itself.
    # Returning True allows Home Assistant to remove the device from the registry.
    return True
```

Implementing this function will enable the "Delete" button on the device page in the Home Assistant UI for the PEGELONLINE stations, allowing users to clean up stale entries manually if needed.

_Created at 2025-05-25 11:26:16. Prompt tokens: 6305, Output tokens: 906, Total tokens: 8600_
