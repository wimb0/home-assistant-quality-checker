# evohome: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires that integrations check during initialization if they can be set up correctly and raise specific `ConfigEntry` exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) to inform the user and Home Assistant about the nature of any failure.

This rule applies to the `evohome` integration as it involves communication with a cloud service (`evohome-async`) which can fail due to various reasons (authentication, network issues, API errors, misconfiguration).

The `evohome` integration currently does **not** fully follow this rule.
In `homeassistant/components/evohome/__init__.py`, the `async_setup_entry` function initializes an `EvoDataUpdateCoordinator` and calls `await coordinator.async_first_refresh()` to perform an initial data fetch and setup.

```python
# homeassistant/components/evohome/__init__.py
async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Load the Evohome config entry."""

    coordinator = EvoDataUpdateCoordinator(
        hass, _LOGGER, config_entry=config_entry, name=f"{DOMAIN}_coordinator"
    )

    await coordinator.async_first_refresh() # Attempts initial setup and refresh

    if not coordinator.last_update_success: # Checks if the refresh was successful
        _LOGGER.error(f"Failed to fetch initial data: {coordinator.last_exception}")
        return False # <--- PROBLEM: Returns False instead of raising a specific ConfigEntry exception

    config_entry.runtime_data = {"coordinator": coordinator}
    # ...
    return True
```

The issue is that if `coordinator.async_first_refresh()` fails (either during its internal `_async_setup` phase or `_async_update_data` phase), the `coordinator.last_update_success` flag will be `False`, and `async_setup_entry` simply returns `False`. Returning `False` signals a generic setup failure to Home Assistant but doesn't provide the specific reasons required by the rule (e.g., temporary issue, authentication problem, or permanent error). This prevents Home Assistant from taking appropriate actions like scheduling retries or initiating a re-authentication flow.

The `coordinator.async_first_refresh()` method itself (in `homeassistant/components/evohome/coordinator.py`) might propagate `ConfigEntryAuthFailed` or `ConfigEntryError` if its internal `_async_update_data` method raises them and the `raise_on_auth_failed=True` / `raise_on_entry_error=True` flags are used during the refresh. However:
1.  Failures within the coordinator's `_async_setup` method (e.g., an `IndexError` for `location_idx`, or an initial `client.update` failure) are wrapped in `UpdateFailed` by `_async_setup`, then caught by the base `DataUpdateCoordinator.__wrap_async_setup`. This sets `coordinator.last_exception` and `coordinator.last_update_success = False` but does not propagate a specific `ConfigEntry*` exception out of `coordinator.async_first_refresh`.
2.  If `_async_update_data` (via `_update_v2_api_state`) encounters an `evohomeasync2.EvohomeError` (which can include auth errors or API issues), it currently raises `UpdateFailed`. This exception is caught by the base `DataUpdateCoordinator._async_refresh`, which then sets `coordinator.last_update_success = False` and `coordinator.last_exception`, but does not re-raise a `ConfigEntry*` exception unless `_async_update_data` itself raised one.

In both scenarios, `async_setup_entry` relies on `coordinator.last_update_success` and then incorrectly returns `False`. It should instead inspect `coordinator.last_exception` (or catch exceptions propagated by `coordinator.async_first_refresh`) and raise the appropriate `ConfigEntryNotReady`, `ConfigEntryAuthFailed`, or `ConfigEntryError`.

## Suggestions

To make the `evohome` integration compliant with the `test-before-setup` rule, the `async_setup_entry` function in `homeassistant/components/evohome/__init__.py` needs to be modified to handle initialization failures correctly by raising the appropriate `ConfigEntry*` exceptions.

1.  **Modify `async_setup_entry` to handle exceptions and `last_exception`:**

    The primary change is in `async_setup_entry` to catch exceptions propagated from `coordinator.async_first_refresh()` and to interpret `coordinator.last_exception` if `coordinator.last_update_success` is `False`.

    ```python
    # homeassistant/components/evohome/__init__.py
    import evohomeasync2 as ec2 # Add this import if not already present
    from http import HTTPStatus # Add this import
    from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady, ConfigEntryError # Ensure these are imported
    from evohomeasync2.exceptions import EvohomeError, BadUserCredentialsError, AuthenticationFailedError, ApiRequestFailedError # Specific exceptions from the library
    from homeassistant.helpers.update_coordinator import UpdateFailed # If checking for UpdateFailed type

    async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
        """Load the Evohome config entry."""

        coordinator = EvoDataUpdateCoordinator(
            hass, _LOGGER, config_entry=config_entry, name=f"{DOMAIN}_coordinator"
        )

        try:
            await coordinator.async_first_refresh()
        except ConfigEntryAuthFailed: # If coordinator.async_first_refresh directly raises this
            raise
        except ConfigEntryNotReady: # If coordinator.async_first_refresh directly raises this
            raise
        except ConfigEntryError: # If coordinator.async_first_refresh directly raises this
            raise
        # Catch other potential library-specific exceptions if async_first_refresh doesn't convert them
        except BadUserCredentialsError as ex:
            raise ConfigEntryAuthFailed("Authentication failed during setup") from ex
        except AuthenticationFailedError as ex:
            if ex.status == HTTPStatus.TOO_MANY_REQUESTS:
                raise ConfigEntryNotReady("API rate limit exceeded during setup") from ex
            raise ConfigEntryAuthFailed(f"Authentication problem during setup: {ex}") from ex
        except ApiRequestFailedError as ex:
            # Check for specific status codes that might indicate a temporary issue
            # For example, 50x errors might be ConfigEntryNotReady
            raise ConfigEntryNotReady(f"API request failed during setup: {ex}") from ex
        except EvohomeError as ex: # More general library error
            raise ConfigEntryNotReady(f"Evohome library error during setup: {ex}") from ex
        # No specific exception was raised by async_first_refresh itself,
        # but an internal failure might have occurred (e.g., in coordinator._async_setup).
        if not coordinator.last_update_success:
            ex = coordinator.last_exception
            _LOGGER.error(f"Failed to fetch initial data: {ex}")

            # Unwrap UpdateFailed if necessary
            actual_ex = ex.__cause__ if isinstance(ex, UpdateFailed) else ex

            if isinstance(actual_ex, BadUserCredentialsError):
                raise ConfigEntryAuthFailed("Invalid credentials") from actual_ex
            if isinstance(actual_ex, AuthenticationFailedError):
                if hasattr(actual_ex, 'status') and actual_ex.status == HTTPStatus.TOO_MANY_REQUESTS:
                    raise ConfigEntryNotReady("API rate limit exceeded") from actual_ex
                raise ConfigEntryAuthFailed(f"Authentication failed: {actual_ex}") from actual_ex
            if isinstance(actual_ex, IndexError): # e.g., from location_idx in coordinator._async_setup
                raise ConfigEntryError(f"Configuration error (e.g., invalid location_idx): {actual_ex}") from actual_ex
            if isinstance(actual_ex, (ApiRequestFailedError, EvohomeError)): # General API/library errors
                # These are often transient or indicate the service is unavailable
                raise ConfigEntryNotReady(f"Evohome API communication failed: {actual_ex}") from actual_ex
            
            # Fallback for other types of coordinator.last_exception
            raise ConfigEntryError(f"Evohome setup failed: {actual_ex or ex}") from (actual_ex or ex)

        config_entry.runtime_data = {"coordinator": coordinator}
        await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
        _register_domain_services(hass)
        return True
    ```

2.  **(Optional but Recommended) Improve exception specificity in `EvoDataUpdateCoordinator`:**

    To make the error handling in `async_setup_entry` cleaner and more robust, modify `EvoDataUpdateCoordinator._async_setup()` and `EvoDataUpdateCoordinator._update_v2_api_state()` (which is called by `_async_update_data`) to raise more specific `evohomeasync2` exceptions or even `ConfigEntry*` exceptions directly, instead of always wrapping them in `UpdateFailed`.

    Example for `coordinator.py` (`_update_v2_api_state`):
    ```python
    # homeassistant/components/evohome/coordinator.py
    # ... (import necessary exceptions: ConfigEntryAuthFailed, ConfigEntryNotReady, ConfigEntryError,
    #      BadUserCredentialsError, AuthenticationFailedError, ApiRequestFailedError, EvohomeError from evohomeasync2, HTTPStatus)

    async def _update_v2_api_state(self, *args: Any) -> None:
        try:
            status = await self.loc.update()
        except BadUserCredentialsError as err: # Specific auth error
            raise ConfigEntryAuthFailed("Invalid credentials detected during data update") from err
        except AuthenticationFailedError as err: # Other auth failures
            if err.status == HTTPStatus.TOO_MANY_REQUESTS:
                raise ConfigEntryNotReady("API rate limit exceeded during data update") from err
            raise ConfigEntryAuthFailed(f"Authentication problem during data update: {err}") from err
        except ApiRequestFailedError as err: # Specific API request failures
            # Potentially check err.status for more granular ConfigEntryNotReady vs ConfigEntryError
            raise ConfigEntryNotReady(f"API request failed: {err.message}") from err
        except EvohomeError as err: # General library error, treat as transient
            raise ConfigEntryNotReady(f"Evohome communication error: {err}") from err
        # Removed the old UpdateFailed wrapping for these cases

        self.logger.debug("Status = %s", status)
    ```
    And similarly for `_async_setup` in `coordinator.py`:
    ```python
    # homeassistant/components/evohome/coordinator.py
    async def _async_setup(self) -> None:
        try:
            await self.client.update(dont_update_status=True)
        # Add similar specific exception handling as in _update_v2_api_state
        except BadUserCredentialsError as err:
            raise ConfigEntryAuthFailed("Authentication failed during initial client update") from err
        # ... other specific evohomeasync2 exceptions ...
        except ec2.EvohomeError as err: # General EvohomeError
            raise ConfigEntryNotReady(f"Evohome API error during initial client update: {err}") from err
        # Keep original IndexError handling or map to ConfigEntryError
        # ...
        try:
            self.loc = self.client.locations[loc_idx]
        except IndexError as err:
            # This is a configuration error, not a transient issue.
            raise ConfigEntryError(
                f"Config error: 'location_idx' = {loc_idx}, "
                f"but the valid range is 0-{len(self.client.locations) - 1}."
            ) from err
        # ...
    ```

    If `_async_update_data` (via `_update_v2_api_state`) raises these `ConfigEntry*` exceptions, they will be correctly propagated by `coordinator.async_first_refresh()` due to the `raise_on_auth_failed=True` and `raise_on_entry_error=True` flags used in `_async_refresh`. The `try...except` block in the modified `async_setup_entry` would then catch them directly.
    If `_async_setup` raises a `ConfigEntry*` exception, it would be stored in `coordinator.last_exception`, and the `if not coordinator.last_update_success:` block in `async_setup_entry` would handle it.

By implementing these changes, the `evohome` integration will correctly report the status of its setup attempt, allowing Home Assistant and the user to respond appropriately to failures.

---

_Created at 2025-05-29 11:49:52. Prompt tokens: 21882, Output tokens: 3072, Total tokens: 35046._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
