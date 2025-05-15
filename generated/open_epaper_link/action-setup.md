# open_epaper_link: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `action-setup` rule requires that service actions are registered in the `async_setup` platform setup method, rather than in `async_setup_entry`. This ensures that services are discoverable and can provide informative errors even if the corresponding configuration entry is not loaded.

This rule applies to the `open_epaper_link` integration as it registers several custom services (e.g., `drawcustom`, `setled`, `reboot_ap`).

Currently, the `open_epaper_link` integration does **not** follow this rule.
-   In `homeassistant/components/open_epaper_link/__init__.py`, the services are set up by calling `await async_setup_services(hass)` within the `async_setup_entry` function (line 28).
-   Services are correspondingly unloaded by calling `await async_unload_services(hass)` within the `async_unload_entry` function (line 94).
-   There is no `async_setup` function defined in `homeassistant/components/open_epaper_link/__init__.py` where these services could be registered.

This means that the services provided by `open_epaper_link` are only available when a configuration entry is successfully loaded. If the entry fails to load, the services become unavailable, and automations using them might not be validated correctly or provide clear feedback to the user.

Furthermore, service handlers like `drawcustom_service` in `services.py` currently fetch the `Hub` instance using a helper `get_hub()` which relies on `hass.data[DOMAIN]` being populated during `async_setup_entry`. If services were called without a loaded entry, this would currently raise a `HomeAssistantError` instead of the prescribed `ServiceValidationError`, and it doesn't explicitly check the `ConfigEntryState`.

## Suggestions

To make the `open_epaper_link` integration compliant with the `action-setup` rule, the following changes are recommended:

1.  **Modify `homeassistant/components/open_epaper_link/__init__.py`:**
    *   Add an `async_setup` function. This function should be responsible for registering the services.
    *   Move the call `await async_setup_services(hass)` from `async_setup_entry` to this new `async_setup` function.
    *   Remove the call `await async_unload_services(hass)` from `async_unload_entry`. Services registered in `async_setup` are generally not removed when a config entry is unloaded.
    *   Ensure `async_setup` returns `True` on successful setup.
    *   Add necessary imports: `from homeassistant.config_entries import ConfigEntryState` and `from homeassistant.exceptions import ServiceValidationError`.

    ```python
    # In homeassistant/components/open_epaper_link/__init__.py

    # Add these imports if not already present at the top
    # from homeassistant.config_entries import ConfigEntryState # Likely needed in services.py
    # from homeassistant.exceptions import ServiceValidationError # Likely needed in services.py
    from homeassistant.helpers.typing import ConfigType # For async_setup signature

    # ... (other imports)

    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up OpenEPaperLink services."""
        await async_setup_services(hass)
        return True

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Set up OpenEPaperLink integration from a config entry."""
        # ...
        # REMOVE: await async_setup_services(hass) from here
        # ...
        return True

    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Unload the integration when removed or restarted."""
        # ...
        if unload_ok:
            await hub.shutdown()
            # REMOVE: await async_unload_services(hass)
            hass.data[DOMAIN].pop(entry.entry_id)
        # ...
        return unload_ok
    ```

2.  **Modify `homeassistant/components/open_epaper_link/services.py`:**
    *   Update service handlers (e.g., `drawcustom_service`, `setled_service`, and any helpers like `get_hub` or functions in `util.py` that rely on the hub) to correctly validate the config entry state.
    *   Since `open_epaper_link` is `single_config_entry: true`, service handlers should:
        a.  Retrieve the config entry for the `DOMAIN`.
        b.  If no entry exists, raise `ServiceValidationError("OpenEPaperLink integration is not configured.")`.
        c.  If an entry exists, check its state. If `entry.state is not ConfigEntryState.LOADED`, raise `ServiceValidationError(f"OpenEPaperLink configuration entry '{entry.title}' is not loaded.")`.
        d.  If loaded, retrieve the `Hub` instance from `hass.data[DOMAIN][entry.entry_id]`. If the hub is not found (shouldn't happen if entry is loaded), raise an appropriate `ServiceValidationError`.
    *   Add imports: `from homeassistant.config_entries import ConfigEntryState` and `from homeassistant.exceptions import ServiceValidationError`.

    **Example modification for `get_hub` or within service handlers:**
    ```python
    # In homeassistant/components/open_epaper_link/services.py

    # Add these imports at the top
    from homeassistant.config_entries import ConfigEntryState
    from homeassistant.exceptions import ServiceValidationError, HomeAssistantError # Keep HomeAssistantError if used elsewhere

    # ...

    async def get_hub_validated(hass: HomeAssistant): # Renamed or new helper
        """Get the hub instance from Home Assistant data after validation."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError("OpenEPaperLink integration is not configured.")

        entry = entries[0] # Since single_config_entry is true

        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                f"OpenEPaperLink configuration entry '{entry.title}' is not loaded."
            )

        hub = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if not hub:
            # This case should ideally not be reached if entry.state is LOADED,
            # as async_setup_entry would have populated hass.data.
            raise ServiceValidationError(
                "Hub instance not found. The integration may not be fully initialized."
            )
        return hub

    # Example usage in a service handler:
    async def drawcustom_service(service: ServiceCall) -> None:
        hub = await get_hub_validated(hass) # Use the new validated getter

        # The existing hub.online check can remain as an application-specific check
        if not hub.online:
            raise HomeAssistantError( # Or ServiceValidationError if more appropriate for this specific condition
                "AP is offline. Please check your network connection and AP status."
            )
        # ... rest of the service logic
    ```

    *   Similarly, functions in `util.py` like `send_tag_cmd` and `reboot_ap` that currently access `hass.data[DOMAIN]` directly will need to be adapted. It's often cleaner to have the service handler obtain the validated `hub` instance and pass it to these utility functions.

    **Example for `util.py` function adaptation (if `hub` is passed):**
    ```python
    # In homeassistant/components/open_epaper_link/util.py
    # Assuming hub is now a passed argument after validation in the service

    async def send_tag_cmd(hass: HomeAssistant, hub: Hub, entity_id: str, cmd: str) -> bool: # Added hub parameter
        # REMOVE:
        # entry_id = list(hass.data[DOMAIN].keys())[0]
        # hub = hass.data[DOMAIN][entry_id]

        if not hub.online: # This check remains relevant
            _LOGGER.error("Cannot send command: AP is offline")
            return False
        # ... rest of the function using the passed hub
    ```
    If `hub` is not passed, these utility functions would need to replicate the validation logic.

By implementing these changes, the service registration will align with the `action-setup` rule, and the service calls will provide more accurate feedback to the user if the integration or its config entry is not in a ready state.

_Created at 2025-05-14 20:28:40. Prompt tokens: 60606, Output tokens: 2085, Total tokens: 66327_
