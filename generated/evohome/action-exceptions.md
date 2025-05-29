# evohome: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `action-exceptions` rule requires that service actions raise specific exceptions (`ServiceValidationError` for incorrect usage, `HomeAssistantError` for other failures) when they encounter problems, so the user is informed.

This rule applies to the `evohome` integration as it provides several services, both domain-level (e.g., `refresh_system`, `set_system_mode`) and entity-level (e.g., `climate.set_temperature`, `water_heater.set_operation_mode`).

The integration currently does **not** fully follow this rule. The main issues are:

1.  **API Call Error Handling**: The `EvoDataUpdateCoordinator.call_client_api` method, used by most entity service calls (like setting temperature, mode, etc.), catches `evohomeasync2.ApiRequestFailedError` (a type of `EvohomeError`) from the underlying library but then logs the error and returns `None` instead of re-raising it as a `HomeAssistantError`. This means if an API call to the Evohome service fails (e.g., network issue, temporary service outage), the Home Assistant service call will appear to succeed silently to the user, but the requested action will not have been performed.

    *Code Reference (`homeassistant/components/evohome/coordinator.py`):*
    ```python
    async def call_client_api(
        self,
        client_api: Awaitable[dict[str, Any] | None],
        request_refresh: bool = True,
    ) -> dict[str, Any] | None:
        """Call a client API and update the Coordinator state if required."""

        try:
            result = await client_api

        except ec2.ApiRequestFailedError as err: # Catches library error
            self.logger.error(err) # Logs it
            return None # <--- Does NOT raise HomeAssistantError as required
    # ...
    ```

2.  **`refresh_system` Service**: The `force_refresh` service (`refresh_system`) calls `coordinator.async_refresh()`. The `DataUpdateCoordinator.async_refresh()` method is designed to log update failures (like `UpdateFailed`, which is a `HomeAssistantError` subclass) and set `last_update_success = False`, but it does not re-raise these exceptions by default in a way that the service call itself would propagate the error to the user. The service call will complete without an explicit error, even if the refresh failed.

    *Code Reference (`homeassistant/components/evohome/__init__.py`):*
    ```python
    @verify_domain_control(hass, DOMAIN)
    async def force_refresh(call: ServiceCall) -> None:
        """Obtain the latest state data via the vendor's RESTful API."""
        await coordinator.async_refresh()
        # No explicit exception is raised here if coordinator.async_refresh()
        # encounters an UpdateFailed error internally.
    ```

While the integration uses `voluptuous` for schema validation (which handles most `ServiceValidationError` cases for basic input types and ranges at the HA core level), the propagation of runtime errors from the API client to the user via `HomeAssistantError` is missing or incomplete.

## Suggestions

To make the `evohome` integration compliant with the `action-exceptions` rule:

1.  **Modify `EvoDataUpdateCoordinator.call_client_api` to raise `HomeAssistantError`:**
    When `evohomeasync2.EvohomeError` (or its specific subclasses like `ApiRequestFailedError`) is caught, it should be re-raised as `HomeAssistantError`. This will ensure that service calls that rely on this method will correctly report failures to the user.

    *Proposed change in `homeassistant/components/evohome/coordinator.py`:*
    ```python
    from homeassistant.exceptions import HomeAssistantError
    import evohomeasync2 as ec2 # Ensure ec2 is available for exception types

    # ...

    async def call_client_api(
        self,
        client_api: Awaitable[dict[str, Any] | None],
        request_refresh: bool = True,
    ) -> dict[str, Any] | None:
        """Call a client API and update the Coordinator state if required."""
        try:
            result = await client_api
        except ec2.ApiRequestFailedError as err:
            raise HomeAssistantError(f"Evohome API request failed: {err}") from err
        except ec2.EvohomeError as err:  # Catch other relevant evohome library errors
            raise HomeAssistantError(f"An error occurred with the Evohome service: {err}") from err
        # Potentially catch other specific ec2 exceptions if they need distinct handling
        # or messages before being wrapped in HomeAssistantError.

        if request_refresh:
            await self.async_request_refresh()
        return result
    ```

2.  **Modify the `force_refresh` service (`refresh_system`) to raise `HomeAssistantError` on failure:**
    After calling `coordinator.async_refresh()`, check `coordinator.last_update_success`. If the refresh was not successful, raise a `HomeAssistantError`.

    *Proposed change in `homeassistant/components/evohome/__init__.py`:*
    ```python
    from homeassistant.exceptions import HomeAssistantError
    # ...

    @verify_domain_control(hass, DOMAIN)
    async def force_refresh(call: ServiceCall) -> None:
        """Obtain the latest state data via the vendor's RESTful API."""
        await coordinator.async_refresh()
        if not coordinator.last_update_success:
            error_message = "Evohome data refresh failed."
            if coordinator.last_exception: # coordinator.last_exception is set by DataUpdateCoordinator
                error_message += f" Details: {coordinator.last_exception}"
            raise HomeAssistantError(error_message)
    ```

3.  **Review for `ServiceValidationError`:**
    While schema validation handles most input checks, briefly review service handlers for any complex logical conditions between parameters that are not covered by the input schema. If such conditions exist and could lead to incorrect usage, raise `ServiceValidationError` explicitly. For example, the `HomeAssistantError` raised in `EvoController.async_set_hvac_mode` for an "Invalid hvac_mode" might be a candidate if that branch is reachable with user input not caught by HA's schema validation for climate entities. However, this is a lower priority than the `HomeAssistantError` propagation for API failures.

By implementing these changes, particularly the first two, the integration will correctly inform users via exceptions when service actions fail, aligning with the `action-exceptions` rule.

---

_Created at 2025-05-29 12:41:16. Prompt tokens: 21823, Output tokens: 1632, Total tokens: 29772._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
