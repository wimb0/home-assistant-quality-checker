```markdown
# fritzbox: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **done**                                       |

## Overview

This rule requires integrations using config entries to implement the `async_unload_entry` function to properly clean up resources when the integration is unloaded. This is essential for allowing users to remove or reload the integration without needing to restart Home Assistant.

The `fritzbox` integration uses config entries and sets up multiple platforms. It establishes a connection to the FRITZ!Box router using the `pyfritzhome` library via the `FritzboxDataUpdateCoordinator`.

Reviewing the provided code:

*   The `homeassistant/components/fritzbox/__init__.py` file contains the standard `async_setup_entry` and `async_unload_entry` functions.
*   The `async_unload_entry` function is implemented as required by the rule.
*   Inside `async_unload_entry`, the code explicitly calls `await hass.async_add_executor_job(entry.runtime_data.fritz.logout)`. This line is crucial as it logs out from the FRITZ!Box device, closing the connection managed by the `pyfritzhome` library, which is the main resource held by the integration. Using `async_add_executor_job` is appropriate as `pyfritzhome.logout` is a potentially blocking synchronous call.
*   The function also calls `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)`. This ensures that all entities and platforms associated with this config entry are properly unloaded, which handles the cleanup of platform-specific resources like listeners added to the coordinator (e.g., `coordinator.async_add_listener` calls in the platform setup files like `binary_sensor.py`, `cover.py`, etc.).
*   The function returns the result of `hass.config_entries.async_unload_platforms`, which correctly indicates whether the unloading process was successful.
*   Although not strictly required by this specific rule but good practice, the `async_setup_entry` function also registers a listener using `entry.async_on_unload` for `EVENT_HOMEASSISTANT_STOP`. This ensures the `fritz.logout()` is called even if Home Assistant is stopped unexpectedly, in addition to being called during a user-initiated unload via `async_unload_entry`.

Based on the presence and correct implementation of `async_unload_entry` including resource cleanup (`logout`) and platform unloading, the `fritzbox` integration fully complies with this rule.

## Suggestions

No suggestions needed. The integration correctly implements config entry unloading.
```

_Created at 2025-05-25 11:34:26. Prompt tokens: 19015, Output tokens: 659, Total tokens: 20776_
