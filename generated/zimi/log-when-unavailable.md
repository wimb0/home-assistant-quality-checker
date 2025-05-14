# zimi: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [zimi](https://www.home-assistant.io/integrations/zimi/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `log-when-unavailable` rule requires that an integration logs a message at `INFO` level when a connected device or service becomes unavailable, and another `INFO` message when it becomes available again. Each state transition (unavailable/available) should be logged only once to avoid spamming the logs.

This rule applies to the `zimi` integration because it communicates with a Zimi Cloud Controller, which is a network device that can become unavailable (e.g., due to network issues, power loss to the controller). If the controller is unreachable, all entities provided by the integration will also become unavailable.

The `zimi` integration currently does not fully follow this rule.
*   During initial setup (`async_setup_entry` in `__init__.py`), if the connection to the Zimi Controller fails, a `ConfigEntryNotReady` exception is raised. Home Assistant core logs this as a warning, but this is related to setup failure, not runtime unavailability after a successful setup.
*   The core of the integration relies on the `zcc-helper` library, specifically the `ControlPoint` class, to manage the connection to the Zimi controller. While the `zcc-helper` library itself might log connection state changes (e.g., `zcc.controlpoint` logger might emit "ZCC connection state changed to: ..."), the `zimi` integration (i.e., using the `homeassistant.components.zimi` logger) does not explicitly log these events at `INFO` level as per the rule's requirements ("the integration should log").
*   Individual entities (`ZimiEntity` in `entity.py`) determine their availability based on `self._device.is_connected`, which in turn depends on the `ControlPoint`'s connection status. However, there is no logic within `ZimiEntity` or at the central `ControlPoint` management level in `__init__.py` to track the availability state and log INFO messages specifically when the Zimi controller (the "service") becomes unavailable and then available again.

The rule provides examples for integrations using `DataUpdateCoordinator` (which `zimi` does not use for primary data fetching) or entities updating via `async_update`. For a push-based integration like `zimi` where a central controller's availability is key, the most suitable approach is to monitor the connection state of the `ControlPoint` object and log changes.

## Suggestions

To make the `zimi` integration compliant with the `log-when-unavailable` rule, the following changes are recommended, focusing on monitoring the connection state of the `ControlPoint` object:

1.  **Define Keys for State Management:**
    In `homeassistant/components/zimi/__init__.py` (or `const.py`), define a key for managing the logged state:
    ```python
    # In __init__.py or const.py
    ZCC_UNAVAILABLE_LOGGED_KEY = "zimi_zcc_unavailable_logged"
    ZCC_CALLBACK_REFERENCE_KEY = "zimi_zcc_callback_ref"
    ```

2.  **Implement Connection State Logging in `async_setup_entry`:**
    Modify `async_setup_entry` in `homeassistant/components/zimi/__init__.py` to register a callback with the `ControlPoint` instance (`api`) that logs connection state changes.

    ```python
    # In homeassistant/components/zimi/__init__.py
    import logging # Ensure logging is imported
    # ... other imports
    
    from .const import DOMAIN # If keys are in const.py
    # Define ZCC_UNAVAILABLE_LOGGED_KEY, ZCC_CALLBACK_REFERENCE_KEY here if not in const.py

    _LOGGER = logging.getLogger(__name__)

    async def async_setup_entry(hass: HomeAssistant, entry: ZimiConfigEntry) -> bool:
        """Connect to Zimi Controller and register device."""
        # ... (existing connection logic) ...
        try:
            api = await async_connect_to_controller(
                host=entry.data[CONF_HOST],
                port=entry.data[CONF_PORT],
            )
        except ControlPointError as error:
            raise ConfigEntryNotReady(f"Zimi setup failed: {error}") from error

        _LOGGER.debug("\n%s", api.describe())
        entry.runtime_data = api

        # --- Start of new code for log-when-unavailable ---
        # Store integration-specific data related to this config entry
        integration_instance_data = hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})
        integration_instance_data[ZCC_UNAVAILABLE_LOGGED_KEY] = False # Initialize as available

        async def _async_log_zcc_connection_state() -> None:
            """Log ZCC connection state changes."""
            # This callback is invoked by the zcc library when its connection state changes.
            # `api` is the ControlPoint instance from the outer scope.
            
            current_zcc_connected = api.connected
            unavailable_logged = integration_instance_data.get(ZCC_UNAVAILABLE_LOGGED_KEY, False)

            if not current_zcc_connected:
                if not unavailable_logged:
                    _LOGGER.info(
                        "Connection to Zimi controller at %s:%s lost",
                        api.description.host,
                        api.description.port,
                    )
                    integration_instance_data[ZCC_UNAVAILABLE_LOGGED_KEY] = True
            else:  # ZCC is connected
                if unavailable_logged:
                    _LOGGER.info(
                        "Connection to Zimi controller at %s:%s re-established",
                        api.description.host,
                        api.description.port,
                    )
                    integration_instance_data[ZCC_UNAVAILABLE_LOGGED_KEY] = False
        
        # Assuming api.connection_callbacks is a list where callbacks can be appended.
        # The callback should be async if the zcc library expects/handles awaitable callbacks.
        # The zcc-helper ControlPoint.connection_callbacks type hint suggests it expects
        # Callable[[], Coroutine[Any, Any, None]]
        if hasattr(api, 'connection_callbacks') and isinstance(api.connection_callbacks, list):
            api.connection_callbacks.append(_async_log_zcc_connection_state)
            integration_instance_data[ZCC_CALLBACK_REFERENCE_KEY] = _async_log_zcc_connection_state
            _LOGGER.debug("Registered ZCC connection state callback")
        else:
            _LOGGER.warning(
                "Could not register ZCC connection state callback: "
                "api.connection_callbacks not found or not a list."
            )
        # --- End of new code ---

        # ... (existing device registry and platform setup) ...
        # device_registry = dr.async_get(hass)
        # ...

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.debug("Zimi setup complete")
        return True
    ```

3.  **Clean Up Callback in `async_unload_entry`:**
    Modify `async_unload_entry` in `homeassistant/components/zimi/__init__.py` to remove the registered callback and clean up stored data.

    ```python
    # In homeassistant/components/zimi/__init__.py

    async def async_unload_entry(hass: HomeAssistant, entry: ZimiConfigEntry) -> bool:
        """Unload a config entry."""
        api = entry.runtime_data

        # --- Start of new code for log-when-unavailable cleanup ---
        integration_instance_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if integration_instance_data:
            callback_to_remove = integration_instance_data.pop(ZCC_CALLBACK_REFERENCE_KEY, None)
            if callback_to_remove and hasattr(api, 'connection_callbacks') and \
               isinstance(api.connection_callbacks, list):
                try:
                    api.connection_callbacks.remove(callback_to_remove)
                    _LOGGER.debug("Unregistered ZCC connection state callback")
                except ValueError:
                    _LOGGER.debug("ZCC connection state callback not found for removal.")
            
            # Clean up other stored data
            integration_instance_data.pop(ZCC_UNAVAILABLE_LOGGED_KEY, None)
            if not integration_instance_data: # If dict is empty
                hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
            if not hass.data.get(DOMAIN, {}): # If DOMAIN dict is empty
                hass.data.pop(DOMAIN, None)
        # --- End of new code ---

        api.disconnect()
        return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    ```

**Explanation of Changes:**
*   The `ControlPoint` object (`api`) from the `zcc-helper` library is assumed to manage the connection to the Zimi Controller and provide a mechanism (e.g., `api.connection_callbacks`) to notify about connection state changes. The `zcc-helper` library's `ControlPoint.connection_callbacks` is a list that can be appended to.
*   An asynchronous callback function (`_async_log_zcc_connection_state`) is defined within `async_setup_entry`. This function checks the controller's connection status (`api.connected`).
*   It uses a flag (`integration_instance_data[ZCC_UNAVAILABLE_LOGGED_KEY]`) stored in `hass.data` (scoped to the specific config entry) to remember if the "unavailable" state has already been logged. This ensures logging happens only once per state transition.
*   When the controller becomes disconnected, and it hasn't been logged as such, an `INFO` message is logged. The flag is then set.
*   When the controller reconnects, and it was previously logged as disconnected, an `INFO` message is logged. The flag is then reset.
*   The callback is registered by appending it to `api.connection_callbacks`. A reference is stored to allow for deregistration.
*   In `async_unload_entry`, the callback is removed from `api.connection_callbacks`, and the associated state in `hass.data` is cleaned up. This is important to prevent memory leaks or incorrect behavior if the config entry is reloaded.

These changes would ensure that the `zimi` integration itself logs the availability status of the Zimi Controller, adhering to the `log-when-unavailable` rule.

_Created at 2025-05-14 14:51:40. Prompt tokens: 7964, Output tokens: 2518, Total tokens: 19402_
