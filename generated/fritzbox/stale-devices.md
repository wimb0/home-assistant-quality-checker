```markdown
# fritzbox: stale-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [stale-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/stale-devices) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that when a device is removed from a hub or account, it should also be removed from Home Assistant's device registry. If automatic removal isn't feasible or reliable, the integration should implement `async_remove_config_entry_device` to allow manual removal by the user.

The `fritzbox` integration uses a `DataUpdateCoordinator` (`FritzboxDataUpdateCoordinator`) to fetch data from the FRITZ!Box API. The FRITZ!Box API provides a list of active devices.

The integration correctly implements logic in the `FritzboxDataUpdateCoordinator` (`coordinator.py`) to detect and remove devices and entities that are no longer returned by the FRITZ!Box API.

Specifically, in the `_async_update_data` method (lines 94-127 in `coordinator.py`), after fetching the `new_data`, it compares the keys (AINs) in the `new_data.devices` and `new_data.templates` dictionaries with the keys in the previous `self.data`. If any keys are present in the old data but missing in the new data (indicating the device/template has been removed from the FRITZ!Box), it calls the `cleanup_removed_devices` method.

The `cleanup_removed_devices` method (lines 64-92 in `coordinator.py`) iterates through the entity registry and device registry entries associated with the config entry. For each entity, it checks if its AIN is still present in the list of `available_ains` from the latest API fetch. If not, it removes the entity registry entry using `entity_reg.async_remove`. Similarly, for each device, it checks if its identifier (based on the AIN) is present in the list of `available_main_ains` from the latest API fetch. If not, it removes the device registry entry's association with the config entry using `device_reg.async_update_device(device.id, remove_config_entry_id=self.config_entry.entry_entry_id)`. This effectively removes the device from Home Assistant if no other integrations are linked to it.

Furthermore, the integration also implements `async_remove_config_entry_device` in `__init__.py` (lines 64-73). This function allows users to attempt manual device removal from the Home Assistant UI. The implementation checks if the device's AIN is still present in the `coordinator.data.devices` or `coordinator.data.templates`. If the AIN *is* found in the coordinator's current data, it returns `False`, preventing the manual removal. If the AIN is *not* found, it returns `True`, allowing the removal. While this differs from the rule's example (which suggests allowing removal if the integration hasn't received recent updates), it is appropriate in this case because the integration already performs automatic removal based on the API's list of active devices. Allowing manual removal *only* when the device is already gone from the API list (and thus likely already subject to automatic removal) serves as a safeguard but isn't strictly necessary for the core "stale devices are removed" requirement, which is met by the automatic cleanup.

Given that the integration proactively identifies and removes devices and entities no longer available via the FRITZ!Box API, it fully satisfies the core requirement of the `stale-devices` rule.

## Suggestions

No suggestions needed. The integration correctly handles the removal of stale devices.
```

_Created at 2025-05-25 11:38:05. Prompt tokens: 19400, Output tokens: 868, Total tokens: 21630_
