# evohome: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `action-setup` rule requires that service actions are registered in the `async_setup` function of an integration, rather than `async_setup_entry`. This ensures that services are always available for validation, even if the configuration entry for the integration is not loaded. The service handlers should then validate if the targeted config entry is loaded and raise `ServiceValidationError` if not.

The `evohome` integration registers services in two places, both of which are problematic with respect to this rule:

1.  **Domain-level services**: Services like `REFRESH_SYSTEM`, `SET_SYSTEM_MODE`, and `RESET_SYSTEM` are registered via the `_register_domain_services` function in `homeassistant/components/evohome/__init__.py`. This function is called from `async_setup_entry`.
    ```python
    # homeassistant/components/evohome/__init__.py
    async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
        # ...
        _register_domain_services(hass) # Problem: Called from async_setup_entry
        return True

    @callback
    def _register_domain_services(hass: HomeAssistant) -> None:
        # ...
        hass.services.async_register(DOMAIN, EvoService.REFRESH_SYSTEM, force_refresh)
        # ...
    ```

2.  **Entity-level services**: Services like `SET_ZONE_OVERRIDE` and `RESET_ZONE_OVERRIDE` (internally `clear_zone_override`) are registered for `climate` entities in `homeassistant/components/evohome/climate.py` using `platform.async_register_entity_service`. This registration is initiated from the `async_setup_entry` function of the `climate` platform for `evohome`.
    ```python
    # homeassistant/components/evohome/climate.py
    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        # ...
        await _register_entity_services(tcs) # Problem: Called from climate.async_setup_entry
    
    async def _register_entity_services(tcs: evo.ControlSystem) -> None:
        platform = async_get_current_platform()
        platform.async_register_entity_service( # Problem: Service registration effectively tied to async_setup_entry
            EvoService.RESET_ZONE_OVERRIDE,
            RESET_ZONE_OVERRIDE_SCHEMA,
            "async_reset_zone_override",
            # ...
        )
        # ...
    ```

Because all services are registered as part of the `async_setup_entry` flow (either directly or via platform setup), they do not meet the `action-setup` rule's requirement. If the `evohome` config entry fails to load, these services will not be registered, preventing proper validation of automations or service calls that use them.

The current service handlers also rely on the coordinator being available, which is set up in `async_setup_entry`. If moved to `async_setup`, these handlers would need to explicitly fetch the config entry and check its loaded state.

## Suggestions

To make the `evohome` integration compliant with the `action-setup` rule, the registration of all its services needs to be moved to the `async_setup` function in `homeassistant/components/evohome/__init__.py`. The service handlers must also be updated to validate the config entry's state.

### 1. Modify Domain-Level Services

Move the registration of services like `REFRESH_SYSTEM`, `SET_SYSTEM_MODE`, and `RESET_SYSTEM` from `_register_domain_services` (and thus from `async_setup_entry`) to `async_setup`.

**In `homeassistant/components/evohome/__init__.py`:**

```python
from homeassistant.config_entries import ConfigEntryState # Add this import
from homeassistant.exceptions import ServiceValidationError # Add this import
# ... other imports ...

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up evohome integration and its services."""

    if not hass.config_entries.async_entries(DOMAIN) and DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )

    # Define service handlers here or import/reference them
    # These handlers need to be adapted to fetch and validate the config entry.

    async def _hass_get_coordinator(hass_obj: HomeAssistant) -> EvoDataUpdateCoordinator:
        """Helper to get the coordinator, ensuring entry is loaded."""
        # evohome is single_config_entry: true
        entries = hass_obj.config_entries.async_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError(
                f"The {DOMAIN} integration has not been configured."
            )
        
        entry = entries[0]
        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                f"The {DOMAIN} config entry is not loaded (current state: {entry.state})."
            )
        
        if "coordinator" not in entry.runtime_data:
            # This should ideally not happen if state is LOADED
            raise ServiceValidationError(
                f"The {DOMAIN} coordinator is not available. Please reload the integration."
            )
        return entry.runtime_data["coordinator"]

    async def handle_refresh_system(call: ServiceCall) -> None:
        """Obtain the latest state data via the vendor's RESTful API."""
        coordinator = await _hass_get_coordinator(hass)
        await coordinator.async_refresh()

    async def handle_set_system_mode(call: ServiceCall) -> None:
        """Set the system mode."""
        coordinator = await _hass_get_coordinator(hass)
        
        assert coordinator.tcs is not None # Should be true if coordinator is available
        
        # The original logic dispatches a signal. This can be kept if appropriate,
        # or the action can be performed directly using the coordinator.
        # For simplicity, direct action:
        # mode = call.data.get(ATTR_MODE)
        # period = call.data.get(ATTR_PERIOD) # This needs conversion from dict to timedelta
        # duration = call.data.get(ATTR_DURATION) # This needs conversion from dict to timedelta
        # await coordinator.tcs.set_mode(mode, until=...) # Example
        # The original dispatcher logic might be better to keep central control via EvoController
        payload = {
            "unique_id": coordinator.tcs.id, # This implies the service targets the controller
            "service": call.service,
            "data": call.data,
        }
        async_dispatcher_send(hass, DOMAIN, payload)

    hass.services.async_register(DOMAIN, EvoService.REFRESH_SYSTEM, handle_refresh_system)

    # Retrieve allowed modes for schema building if needed, or simplify.
    # This part is tricky as `coordinator.tcs` is not available in `async_setup` directly.
    # One option is to register with a generic schema initially, or if schema depends
    # on loaded entry, it might imply some services can only be fully defined post-load,
    # which slightly complicates this rule. However, the service *registration* must be in async_setup.
    # For now, let's assume fixed schemas or schemas that don't depend on live data.
    # The original code dynamically builds `system_mode_schemas`.
    # If this dynamic schema generation is essential, it suggests that
    # `hass.services.async_set_service_schema` might be needed after entry load,
    # but the initial registration must be in `async_setup`.
    # A simpler approach is to use the widest possible schema if dynamic parts are complex.
    # For demonstration, using the existing EvoService enum:
    
    # Example for SET_SYSTEM_MODE (schema might need adjustment or dynamic update later)
    # This is a simplified schema example; the original is more complex.
    # You might need to fetch the coordinator inside `handle_set_system_mode` to check allowed modes
    # if validation is strict.
    set_system_mode_schema = vol.Schema({
        vol.Required(ATTR_MODE): cv.string, # Keep it simple or adapt from services.yaml
        vol.Optional(ATTR_PERIOD): cv.time_period_dict,
        vol.Optional(ATTR_DURATION): cv.time_period_dict,
    })

    hass.services.async_register(
        DOMAIN,
        EvoService.SET_SYSTEM_MODE,
        handle_set_system_mode, # This handler would need access to coordinator and tcs
        schema=set_system_mode_schema # Adjust as per original dynamic schema if possible
    )
    
    # The RESET_SYSTEM service in evohome uses the same `set_system_mode` handler.
    # It effectively sets mode to EvoSystemMode.AUTO_WITH_RESET.
    # The original code registers this only if `EvoSystemMode.AUTO_WITH_RESET` is in `coordinator.tcs.modes`.
    # This dynamic registration based on device capability is a challenge for `async_setup`.
    # One way: Register it always, and the handler checks capability.
    hass.services.async_register(DOMAIN, EvoService.RESET_SYSTEM, handle_set_system_mode)
    # The `handle_set_system_mode` would need to know if it was called for RESET_SYSTEM
    # and then check if `AUTO_WITH_RESET` is supported by the specific TCS.

    return True

# Remove the _register_domain_services function and its call from async_setup_entry.
```
**Note on dynamic schemas/registrations:** The `SET_SYSTEM_MODE` and `RESET_SYSTEM` services have schemas and registration conditions that depend on the capabilities of the connected Evohome system, which are only known after the coordinator has fetched initial data. The rule prefers registration in `async_setup`.
*   **Option 1 (Preferred by rule):** Register all services in `async_setup` with the broadest possible schema. The service handler then performs capability checks and raises `ServiceValidationError` if a specific mode/action is not supported by the hardware.
*   **Option 2 (Compromise):** Register in `async_setup`. After the config entry loads, use `hass.services.async_set_service_schema` to refine the schema if necessary. Conditional registration (`hass.services.async_register` only if feature X exists) is problematic if done outside `async_setup`.

### 2. Modify Entity-Level Services

The entity services (`SET_ZONE_OVERRIDE`, `CLEAR_ZONE_OVERRIDE`) currently registered by the `climate` platform need to be registered in `__init__.py`'s `async_setup`. The `platform.async_register_entity_service` calls in `climate.py` should be removed.

**In `homeassistant/components/evohome/__init__.py` (within `async_setup`):**

```python
# Add these imports to __init__.py if not already present
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_component import EntityComponent

# These schemas are currently in climate.py, move them or make them accessible
# For example, define them in const.py or a shared services.py
# Assuming SET_ZONE_OVERRIDE_SCHEMA and RESET_ZONE_OVERRIDE_SCHEMA are available
from .climate import SET_ZONE_OVERRIDE_SCHEMA, RESET_ZONE_OVERRIDE_SCHEMA # Or move definitions

# ... inside async_setup function ...

async def _validate_entity_and_get_config_entry(hass_obj: HomeAssistant, entity_id_str: str) -> ConfigEntry:
    """Helper to validate entity and its config entry state."""
    ent_reg = er.async_get(hass_obj)
    registry_entry = ent_reg.async_get(entity_id_str)

    if not registry_entry:
        raise ServiceValidationError(f"Entity '{entity_id_str}' not found in entity registry.")
    
    if not registry_entry.config_entry_id:
        # Should not happen for properly registered entities
        raise ServiceValidationError(f"Entity '{entity_id_str}' is not associated with a config entry.")

    config_entry = hass_obj.config_entries.async_get_entry(registry_entry.config_entry_id)
    if not config_entry:
        raise ServiceValidationError(
            f"Config entry '{registry_entry.config_entry_id}' not found for entity '{entity_id_str}'."
        )

    if config_entry.domain != DOMAIN:
        # Should not happen if service call is for this domain's entities
        raise ServiceValidationError(
            f"Entity '{entity_id_str}' belongs to domain '{config_entry.domain}', expected '{DOMAIN}'."
        )

    if config_entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            f"The config entry for entity '{entity_id_str}' is not loaded (current state: {config_entry.state})."
        )
    return config_entry


async def handle_set_zone_override(call: ServiceCall) -> None:
    entity_id = call.data.get(ATTR_ENTITY_ID)
    if not entity_id: # Schema should enforce this
        raise ServiceValidationError(f"'{ATTR_ENTITY_ID}' is required.")

    await _validate_entity_and_get_config_entry(hass, entity_id)
    
    climate_comp: EntityComponent | None = hass.data.get(Platform.CLIMATE)
    if not climate_comp or not (entity := climate_comp.get_entity(entity_id)):
        raise ServiceValidationError(f"Climate entity {entity_id} not found or climate platform not loaded.")

    if not hasattr(entity, "async_set_zone_override"):
        raise ServiceValidationError(f"Entity {entity_id} does not support 'async_set_zone_override'.")

    # Extract parameters from call.data, matching the entity method's signature
    setpoint = call.data[ATTR_SETPOINT] # From schema
    duration_dict = call.data.get(ATTR_DURATION) # From schema (optional)
    
    duration_td = None
    if duration_dict:
        duration_td = cv.time_period(duration_dict) # Convert dict to timedelta

    await entity.async_set_zone_override(setpoint=setpoint, duration=duration_td)


async def handle_clear_zone_override(call: ServiceCall) -> None:
    entity_id = call.data.get(ATTR_ENTITY_ID)
    if not entity_id: # Schema should enforce this
        raise ServiceValidationError(f"'{ATTR_ENTITY_ID}' is required.")

    await _validate_entity_and_get_config_entry(hass, entity_id)

    climate_comp: EntityComponent | None = hass.data.get(Platform.CLIMATE)
    if not climate_comp or not (entity := climate_comp.get_entity(entity_id)):
        raise ServiceValidationError(f"Climate entity {entity_id} not found or climate platform not loaded.")

    if not hasattr(entity, "async_reset_zone_override"): # Method name in EvoZone
        raise ServiceValidationError(f"Entity {entity_id} does not support 'async_reset_zone_override'.")

    await entity.async_reset_zone_override()


hass.services.async_register(
    DOMAIN, # Service is registered on the integration's domain
    EvoService.SET_ZONE_OVERRIDE,
    handle_set_zone_override,
    schema=SET_ZONE_OVERRIDE_SCHEMA, # Ensure this schema is imported/defined
)

hass.services.async_register(
    DOMAIN,
    EvoService.RESET_ZONE_OVERRIDE, # This is "clear_zone_override"
    handle_clear_zone_override,
    schema=RESET_ZONE_OVERRIDE_SCHEMA, # Ensure this schema is imported/defined
)
```

**In `homeassistant/components/evohome/climate.py`:**
*   Remove the `_register_entity_services` function.
*   Remove the call to `_register_entity_services` from `climate.async_setup_entry`.
*   The entity methods (`async_set_zone_override`, `async_reset_zone_override` on `EvoZone`) will remain as they contain the actual logic.
*   The service schemas (`SET_ZONE_OVERRIDE_SCHEMA`, `RESET_ZONE_OVERRIDE_SCHEMA`) would ideally be moved to a shared location (e.g., `const.py` or a new `services.py` in the `evohome` component folder) or defined directly in `__init__.py` if they are not too large.

These changes ensure that all `evohome` services are registered when Home Assistant starts and the `evohome` component is set up, regardless of the config entry's status. The service handlers then explicitly check for a loaded config entry before proceeding, providing clearer error messages to the user if the service cannot be executed.

---

_Created at 2025-05-29 11:40:53. Prompt tokens: 21947, Output tokens: 4153, Total tokens: 32658._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
