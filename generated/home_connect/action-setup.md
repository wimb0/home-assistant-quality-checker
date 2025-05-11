# home_connect: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **todo**                                                                 |

## Overview

The rule `action-setup` applies to the `home_connect` integration because it defines and registers custom service actions (e.g., `start_program`, `change_setting`, `set_program_and_options`).

The integration partially follows this rule:

1.  **Service Registration:** The services are correctly registered within the `async_setup` function in `homeassistant/components/home_connect/__init__.py`. This is achieved by calling `register_actions(hass)`, a function imported from `homeassistant/components/home_connect/services.py`, which in turn calls `hass.services.async_register` for each service. This ensures services are available globally, regardless of whether a config entry is loaded.
    ```python
    # __init__.py
    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up Home Connect component."""
        register_actions(hass) # Correctly calls registration here
        return True
    ```
    ```python
    # services.py
    def register_actions(hass: HomeAssistant) -> None:
        """Register custom actions."""
        hass.services.async_register(
            DOMAIN,
            SERVICE_OPTION_ACTIVE,
            async_service_option_active,
            schema=SERVICE_OPTION_SCHEMA,
        )
        # ... and other services like SERVICE_SETTING, SERVICE_START_PROGRAM, etc.
    ```

2.  **Config Entry Handling in Service Calls:** The service handlers, such as `async_service_setting` or `async_service_set_program_and_options` in `services.py`, use a helper function `_get_client_and_ha_id`. This helper correctly retrieves the `ConfigEntry` associated with the `device_id` passed in the service call. It also raises appropriate `ServiceValidationError` if the device or its associated config entry cannot be found.

3.  **Missing "Entry Loaded" Check:** The primary deviation from the rule's best practice is within the `_get_client_and_ha_id` function in `services.py`. After successfully finding the `ConfigEntry` (aliased as `entry`), the function does not explicitly check if `entry.state is ConfigEntryState.LOADED` before attempting to access `entry.runtime_data.client`.
    ```python
    # services.py - _get_client_and_ha_id function
    # ...
    if entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_found",
            # ...
        ) # Correctly handles entry not found
    
    # THE FOLLOWING CHECK IS MISSING AS PER THE RULE'S GUIDANCE:
    # if entry.state is not ConfigEntryState.LOADED:
    #     raise ServiceValidationError("Configuration entry '{entry.title}' is not loaded.")
    
    ha_id = next(
        (
            identifier[1]
            for identifier in device_entry.identifiers
            if identifier[0] == DOMAIN
        ),
        None,
    )
    if ha_id is None:
        raise ServiceValidationError(...) # Correctly handles appliance not found in entry
    
    return entry.runtime_data.client, ha_id # Accesses runtime_data without an explicit LOADED state check
    ```
    The rule states: "This way we can let the user know why the service action did not work, if the targeted configuration entry is not loaded." If an entry is found but is not in a `LOADED` state (e.g., `SETUP_ERROR`, `NOT_LOADED`, `SETUP_RETRY`), accessing `entry.runtime_data` (which is the coordinator instance) could lead to an `AttributeError` if `runtime_data` was not successfully set during `async_setup_entry`. This would result in a generic error log rather than the user-friendly `ServiceValidationError` specifically indicating the entry is not loaded.

## Suggestions

To fully comply with the `action-setup` rule, the `home_connect` integration should ensure its service handlers explicitly check if the targeted config entry is loaded before attempting to use its runtime data.

Modify the `_get_client_and_ha_id` helper function in `custom_components/home_connect/services.py` (or `homeassistant/components/home_connect/services.py` for core) as follows:

1.  Ensure `ConfigEntryState` is imported:
    ```python
    from homeassistant.config_entries import ConfigEntryState 
    ```

2.  Add the check within the `_get_client_and_ha_id` function:
    ```python
    # custom_components/home_connect/services.py

    # ... other imports
    from homeassistant.config_entries import ConfigEntryState
    # ...

    async def _get_client_and_ha_id(
        hass: HomeAssistant, device_id: str
    ) -> tuple[HomeConnectClient, str]:
        device_registry = dr.async_get(hass)
        device_entry = device_registry.async_get(device_id)
        if device_entry is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="device_entry_not_found",
                translation_placeholders={
                    "device_id": device_id,
                },
            )
        entry: HomeConnectConfigEntry | None = None
        for entry_id in device_entry.config_entries:
            _entry = hass.config_entries.async_get_entry(entry_id)
            assert _entry
            if _entry.domain == DOMAIN:
                entry = cast(HomeConnectConfigEntry, _entry)
                break
        if entry is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="config_entry_not_found",
                translation_placeholders={
                    "device_id": device_id,
                },
            )

        # ADD THIS CHECK:
        if entry.state is not ConfigEntryState.LOADED:
            # Consider adding a new translation key for this specific error in strings.json
            # e.g., "config_entry_not_loaded": "Configuration entry '{entry_title}' is not loaded."
            raise ServiceValidationError(
                translation_domain=DOMAIN, 
                translation_key="config_entry_not_loaded", # Example translation key
                translation_placeholders={"entry_title": entry.title} 
            )

        ha_id = next(
            (
                identifier[1]
                for identifier in device_entry.identifiers
                if identifier[0] == DOMAIN
            ),
            None,
        )
        if ha_id is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="appliance_not_found",
                translation_placeholders={
                    "device_id": device_id,
                },
            )
        
        # It's good practice to also ensure runtime_data is populated,
        # though LOADED state usually implies this from a successful async_setup_entry.
        if entry.runtime_data is None:
            # This state might be unexpected if entry.state is LOADED, but acts as a safeguard.
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="config_entry_runtime_data_missing", # Example translation key
                translation_placeholders={"entry_title": entry.title}
            )
            
        return entry.runtime_data.client, ha_id
    ```

**Reasoning for Suggestion:**
Adding the `if entry.state is not ConfigEntryState.LOADED:` check ensures that if a service is called targeting a config entry that exists but is not currently loaded (e.g., due to a setup error, network issue, or if it's being reconfigured), a clear `ServiceValidationError` is raised. This provides better feedback to the user, as intended by the rule, instead of potentially causing an unhandled `AttributeError` (if `entry.runtime_data` is not set) or other unexpected behavior.

It is also recommended to add the new translation keys (e.g., `config_entry_not_loaded`, `config_entry_runtime_data_missing`) to the `strings.json` (and `translations/en.json`) file for user-friendly error messages.

_Created at 2025-05-10 20:15:59. Prompt tokens: 139671, Output tokens: 2009, Total tokens: 145965_
