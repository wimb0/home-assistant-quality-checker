# evohome: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `config-entry-unloading` rule requires that integrations support config entry unloading, allowing Home Assistant to unload the integration at runtime. This involves implementing the `async_unload_entry` function to clean up any resources (like subscriptions, connections, or registered services) that were set up during `async_setup_entry`.

The `evohome` integration uses config entries (as indicated by `config_flow: true` in `manifest.json` and the presence of `async_setup_entry` in `homeassistant/components/evohome/__init__.py`), so this rule applies.

The integration partially follows the rule:
1.  It implements the `async_unload_entry` function in `homeassistant/components/evohome/__init__.py`.
2.  This function correctly calls `await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)` to unload the platforms (climate, water_heater) that were set up.

However, the integration does not fully follow the rule because it fails to clean up all resources established during `async_setup_entry`. Specifically, the domain-level services registered by the `_register_domain_services` function in `homeassistant/components/evohome/__init__.py` are not unregistered during the unload process.

In `async_setup_entry` (around line 63 of `homeassistant/components/evohome/__init__.py`):
```python
    # ...
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    _register_domain_services(hass) # Domain services are registered here

    return True
```

The `_register_domain_services` function (lines 74-153) registers services like `EvoService.REFRESH_SYSTEM`, `EvoService.RESET_SYSTEM` (conditional), and `EvoService.SET_SYSTEM_MODE` (conditional) using `hass.services.async_register`.

The current `async_unload_entry` function is (lines 66-70):
```python
async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload the Evohome config entry."""

    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
```
This function only unloads the platforms and does not include logic to unregister the domain services. If the config entry is reloaded, `_register_domain_services` would be called again, potentially re-registering services. If the entry is removed, these services would ideally be cleaned up.

## Suggestions

To make the `evohome` integration compliant with the `config-entry-unloading` rule, the domain-level services registered in `_register_domain_services` should be unregistered in `async_unload_entry`.

Here's a suggested approach:

1.  **Modify `_register_domain_services` to track registered services:**
    *   Pass the `config_entry` to `_register_domain_services`.
    *   Store the names of successfully registered services in `config_entry.runtime_data`.
    *   Initialize `config_entry.runtime_data["domain_services"] = []` in `async_setup_entry`.

2.  **Update `async_unload_entry` to unregister these services:**
    *   After successfully unloading platforms (i.e., `unload_ok` is `True`), retrieve the list of registered service names from `config_entry.runtime_data`.
    *   Iterate through this list and call `hass.services.async_remove(DOMAIN, service_name)` for each.

**Example Code Changes:**

**In `homeassistant/components/evohome/__init__.py`:**

```python
# ...
async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Load the Evohome config entry."""

    coordinator = EvoDataUpdateCoordinator(
        hass, _LOGGER, config_entry=config_entry, name=f"{DOMAIN}_coordinator"
    )

    await coordinator.async_first_refresh()

    if not coordinator.last_update_success:
        _LOGGER.error(f"Failed to fetch initial data: {coordinator.last_exception}")  # noqa: G004
        return False

    # Initialize domain_services list in runtime_data
    config_entry.runtime_data = {"coordinator": coordinator, "domain_services": []}

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    _register_domain_services(hass, config_entry) # Pass config_entry

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload the Evohome config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    if unload_ok:
        # Unregister domain services
        registered_services = config_entry.runtime_data.pop("domain_services", [])
        for service_name in registered_services:
            hass.services.async_remove(DOMAIN, service_name)
        
        # It's also good practice to clean up other items from runtime_data if they won't be
        # automatically handled or if they hold significant resources, though Home Assistant
        # clears runtime_data itself after a successful unload.
        # For example: config_entry.runtime_data.pop("coordinator", None)

    return unload_ok


@callback
def _register_domain_services(hass: HomeAssistant, config_entry: ConfigEntry) -> None: # Add config_entry parameter
    """Set up the service handlers for the system/zone operating modes."""

    # _register_domain_services() is safe only whilst "single_config_entry" is true

    # Use coordinator from config_entry.runtime_data directly
    coordinator: EvoDataUpdateCoordinator = config_entry.runtime_data["coordinator"]

    @verify_domain_control(hass, DOMAIN)
    async def force_refresh(call: ServiceCall) -> None:
        # ... (rest of the function as is)
        await coordinator.async_refresh()

    @verify_domain_control(hass, DOMAIN)
    async def set_system_mode(call: ServiceCall) -> None:
        # ... (rest of the function as is)
        async_dispatcher_send(hass, DOMAIN, payload)

    assert coordinator.tcs is not None  # mypy

    hass.services.async_register(DOMAIN, EvoService.REFRESH_SYSTEM, force_refresh)
    config_entry.runtime_data["domain_services"].append(EvoService.REFRESH_SYSTEM)


    # Enumerate which operating modes are supported by this system
    modes = list(coordinator.tcs.allowed_system_modes)

    # Not all systems support "AutoWithReset": register this handler only if required
    if EvoSystemMode.AUTO_WITH_RESET in coordinator.tcs.modes:
        hass.services.async_register(DOMAIN, EvoService.RESET_SYSTEM, set_system_mode)
        config_entry.runtime_data["domain_services"].append(EvoService.RESET_SYSTEM)


    system_mode_schemas = []
    modes = [m for m in modes if m[SZ_SYSTEM_MODE] != EvoSystemMode.AUTO_WITH_RESET]

    # ... (logic for perm_modes, temp_modes as is) ...

    if system_mode_schemas:
        hass.services.async_register(
            DOMAIN,
            EvoService.SET_SYSTEM_MODE,
            set_system_mode,
            schema=vol.Schema(vol.Any(*system_mode_schemas)),
        )
        config_entry.runtime_data["domain_services"].append(EvoService.SET_SYSTEM_MODE)

```

**Why these changes satisfy the rule:**
By implementing these changes, the `async_unload_entry` function will properly clean up the domain-level services that were registered during `async_setup_entry`. This ensures that all significant resources set up by the integration for this config entry are released upon unload, improving system stability and resource management, and allowing for cleaner reloads or removal of the integration.

---

_Created at 2025-05-29 12:42:38. Prompt tokens: 21854, Output tokens: 2036, Total tokens: 29967._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
