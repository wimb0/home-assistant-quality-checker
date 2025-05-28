```markdown
# fritzbox: dynamic-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [dynamic-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires integrations to automatically create entities for devices that are added to the integrated service *after* the integration has been initially set up in Home Assistant. This provides a better user experience as new devices appear automatically without requiring user intervention like reconfiguring the integration.

The `fritzbox` integration implements this behavior by using a `DataUpdateCoordinator` (`FritzboxDataUpdateCoordinator` in `coordinator.py`) to manage fetching device data from the FRITZ!Box. The coordinator's `_async_update_data` method (which calls `_update_fritz_devices`) is responsible for updating the device list. Within `_update_fritz_devices`, the integration compares the newly fetched device list (`device_data.keys()`, `template_data.keys()`) with the previously known devices (`self.data.devices.keys()`, `self.data.templates.keys()`) and stores the AINs (Actor Identification Number) of the newly discovered devices and templates in `self.new_devices` and `self.new_templates`.

Each platform (`binary_sensor.py`, `cover.py`, `switch.py`, `sensor.py`, `light.py`, `button.py`) registers a callback function (`_add_entities`) with the coordinator using `coordinator.async_add_listener(_add_entities)`. This listener is triggered whenever the coordinator successfully updates its data. The `_add_entities` callback in each platform checks `coordinator.new_devices` or `coordinator.new_templates` and uses `async_add_entities` to add entities for any AINs found in these sets that are relevant to that specific platform type (e.g., checking `device.has_switch` in `switch.py`).

This pattern ensures that when a new device or template is added to the FRITZ!Box and detected by the coordinator on a subsequent poll, the registered listener callbacks in the platforms will be invoked, and the relevant entities will be created and added to Home Assistant automatically.

Initial entity creation for devices present at setup is handled by calling `_add_entities` once after the coordinator's first refresh in each platform's `async_setup_entry`, passing the full set of currently known devices/templates.

The implementation fully aligns with the requirements and recommended pattern for handling dynamically added devices.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:35:49. Prompt tokens: 19131, Output tokens: 624, Total tokens: 20589_
