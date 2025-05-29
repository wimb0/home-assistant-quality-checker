# jewish_calendar: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `action-setup` rule mandates that service actions provided by an integration should be registered in the `async_setup` function of the integration. This ensures that the services are discoverable and available for validation (e.g., in automations) even if the integration's configuration entry is not loaded. If a service depends on a specific configuration entry, it should handle cases where the entry might not be loaded, typically by raising a `ServiceValidationError`.

This rule applies to the `jewish_calendar` integration as it defines a service, `count_omer`.

The `jewish_calendar` integration **follows** this rule:

1.  **Service Registration in `async_setup`**:
    The integration's `__init__.py` file correctly calls `async_setup_services(hass)` within its `async_setup` function:
    ```python
    # homeassistant/components/jewish_calendar/__init__.py
    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up the Jewish Calendar service."""
        async_setup_services(hass)  # Service registration initiated here
        return True
    ```
    The `async_setup_services` function, located in `service.py`, then registers the `SERVICE_COUNT_OMER` service:
    ```python
    # homeassistant/components/jewish_calendar/service.py
    def async_setup_services(hass: HomeAssistant) -> None:
        """Set up the Jewish Calendar services."""
        # ...
        hass.services.async_register(
            DOMAIN,
            SERVICE_COUNT_OMER,
            get_omer_count,
            schema=OMER_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )
    ```
    This ensures the service is registered when the integration is set up, independent of any config entry's state.

2.  **Service Dependency on Config Entry**:
    The `count_omer` service, as currently implemented, does not directly depend on data from a `jewish_calendar` config entry.
    *   It accepts parameters like `date`, `nusach`, and `language` directly from the service call.
    *   For determining if it's `after_sunset` (when no specific `date` is provided in the call), the internal helper `is_after_sunset` uses `homeassistant.helpers.sun.get_astral_event_date`. This function defaults to using the global Home Assistant location settings (`hass.config.latitude`, `hass.config.longitude`) if no specific entity's location is provided. The `count_omer` service does not pass any entity-specific location data to it.

    Since the service, in its current design, does not fetch or use data specific to a `jewish_calendar` config entry (like a custom location set within the entry), the part of the rule's example demonstrating how to fetch a config entry by ID and check its loaded state (`entry.state is not ConfigEntryState.LOADED`) is not directly applicable. The service can function based on its input parameters and global HA settings without requiring a loaded `jewish_calendar` config entry.

Therefore, the integration correctly registers its service in `async_setup`, fulfilling the primary requirement of the `action-setup` rule.

*Self-note for reviewer: While the service functions independently of the config entry, there's a potential design inconsistency. Sensors in this integration use the location configured in the `jewish_calendar` entry. The `count_omer` service's `is_after_sunset` helper (for default date scenarios) uses the global HA location. This could lead to different sunset interpretations. If the service were modified to use the config entry's specific location for consistency, it would then need to implement the config entry loading checks described in the rule's example.*

## Suggestions

No suggestions needed for compliance with this specific rule based on the current implementation.

_Created at 2025-05-29 08:01:17. Prompt tokens: 13584, Output tokens: 983, Total tokens: 23675_
