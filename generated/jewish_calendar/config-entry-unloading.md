# jewish_calendar: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `config-entry-unloading` rule requires that integrations support the unloading of their config entries at runtime. This allows users to remove or reload the integration without restarting Home Assistant. This involves implementing the `async_unload_entry` function to clean up all resources, subscriptions, and connections established during the config entry's setup.

The `jewish_calendar` integration **applies** to this rule because it is configured via config entries, as indicated by `config_flow: true` in its `manifest.json` and the presence of `config_flow.py`, as well as `async_setup_entry` and `async_unload_entry` functions in `homeassistant/components/jewish_calendar/__init__.py`.

The integration **fully follows** this rule. Here's a detailed breakdown:

1.  **Implementation of `async_unload_entry`**:
    The integration correctly implements the `async_unload_entry` function in `homeassistant/components/jewish_calendar/__init__.py`:
    ```python
    async def async_unload_entry(
        hass: HomeAssistant, config_entry: JewishCalendarConfigEntry
    ) -> bool:
        """Unload a config entry."""
        return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    ```
    This function is essential for the unloading process.

2.  **Platform Unloading**:
    The call to `await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)` ensures that all entities (sensors and binary sensors defined in `PLATFORMS`) associated with this config entry are properly unloaded. This process includes invoking the `async_will_remove_from_hass` method for each entity.

3.  **Entity-Specific Cleanup**:
    *   For example, in `homeassistant/components/jewish_calendar/binary_sensor.py`, the `JewishCalendarBinarySensor` class manages a timer (`_update_unsub`) created with `event.async_track_point_in_time`. This timer is correctly cancelled in its `async_will_remove_from_hass` method:
        ```python
        # homeassistant/components/jewish_calendar/binary_sensor.py
        async def async_will_remove_from_hass(self) -> None:
            if self._update_unsub:
                self._update_unsub()
                self._update_unsub = None
            return await super().async_will_remove_from_hass()
        ```
    This cleanup is triggered by the platform unloading initiated in `async_unload_entry`.

4.  **Config Entry Update Listener Cleanup**:
    In `async_setup_entry` (within `homeassistant/components/jewish_calendar/__init__.py`), an update listener is registered to handle changes in config entry options:
    ```python
    # homeassistant/components/jewish_calendar/__init__.py
    async def update_listener(
        hass: HomeAssistant, config_entry: JewishCalendarConfigEntry
    ) -> None:
        # Trigger update of states for all platforms
        await hass.config_entries.async_reload(config_entry.entry_id)

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))
    ```
    The `config_entry.add_update_listener` method returns a callback function that, when called, unregisters the listener. By passing this remover callback to `config_entry.async_on_unload`, the integration ensures that the listener is cleaned up automatically when `async_unload_entry` successfully completes (returns `True`). This aligns with the recommended practice mentioned in the rule's documentation.

5.  **Data Cleanup**:
    Resources like `config_entry.runtime_data` (which holds `JewishCalendarData`, including an `hdate.Location` object) are primarily data containers. The `Location` object is created via `hass.async_add_executor_job`, which is a one-time task whose result is stored. These objects do not appear to hold active, long-lived connections or subscriptions that would require explicit closing in `async_unload_entry` beyond the standard garbage collection once the entry and its entities are unloaded.

6.  **Service Handling**:
    Services (e.g., `SERVICE_COUNT_OMER`) are registered in the global `async_setup` function. Their lifecycle is tied to the component's overall load status, not individual config entries. As `async_setup` is not re-run during a config entry reload, these services are not expected to be unregistered in `async_unload_entry`. This is standard Home Assistant behavior.

In summary, the `jewish_calendar` integration correctly implements `async_unload_entry`, handles the unloading of its platforms, and ensures that listeners and other entity-specific resources are properly cleaned up, thereby complying with the `config-entry-unloading` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:14:15. Prompt tokens: 13491, Output tokens: 1229, Total tokens: 20739_
