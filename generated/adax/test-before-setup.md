# adax: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                                                 |

## Overview

The `test-before-setup` rule requires that integrations check during their initialization (`async_setup_entry`) if they can be set up correctly, raising specific exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) to inform the user about the nature of any failure.

This rule applies to the `adax` integration as it involves communication with external devices or cloud services, which can fail for various reasons (network issues, authentication problems, etc.).

The `adax` integration partially follows this rule.
In its `__init__.py`, the `async_setup_entry` function correctly calls `await entry.runtime_data.async_config_entry_first_refresh()`. The `DataUpdateCoordinator.async_config_entry_first_refresh()` method is designed to raise `ConfigEntryNotReady` if the initial data fetch (performed by the coordinator's `_async_update_data` method) fails. This covers scenarios where the device/service is temporarily unavailable.

However, the integration does not fully meet the rule's requirements because the `_async_update_data` methods in `AdaxCloudCoordinator` and `AdaxLocalCoordinator` (defined in `coordinator.py`) do not explicitly catch and translate library-specific exceptions into `ConfigEntryAuthFailed` (for authentication errors) or `ConfigEntryError` (for permanent, non-authentication related setup failures).

**Code References:**

*   **`homeassistant/components/adax/__init__.py`:**
    ```python
    async def async_setup_entry(hass: HomeAssistant, entry: AdaxConfigEntry) -> bool:
        # ...
        await entry.runtime_data.async_config_entry_first_refresh() # Correctly calls first refresh
        # ...
        return True
    ```
    This call handles the `ConfigEntryNotReady` case for general failures during the first data fetch.

*   **`homeassistant/components/adax/coordinator.py` (AdaxCloudCoordinator):**
    ```python
    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from the Adax."""
        rooms = await self.adax_data_handler.get_rooms() or [] # API call
        return {r["id"]: r for r in rooms}
    ```
    This method calls `self.adax_data_handler.get_rooms()`. If this call fails due to, for example, an invalid API token or password, the `adax` library might raise an exception. This coordinator does not catch specific `adax` library exceptions to re-raise them as `ConfigEntryAuthFailed` or `ConfigEntryError`. Any such exception would likely be wrapped as `UpdateFailed` by the base coordinator, leading to `ConfigEntryNotReady`.

*   **`homeassistant/components/adax/coordinator.py` (AdaxLocalCoordinator):**
    ```python
    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Adax."""
        if result := await self.adax_data_handler.get_status(): # API call
            return cast(dict[str, Any], result)
        raise UpdateFailed("Got invalid status from device")
    ```
    Similarly, this method calls `self.adax_data_handler.get_status()`. If this fails due to an invalid local device token or other persistent issue, the `adax_local` library might raise an exception. This is not specifically caught and translated to `ConfigEntryAuthFailed` or `ConfigEntryError`. The explicit `raise UpdateFailed` or a library exception would also lead to `ConfigEntryNotReady`.

The rule implies that different types of errors should be distinguished. For instance, an invalid password should lead to `ConfigEntryAuthFailed`, prompting re-authentication, rather than just a generic "not ready" state.

## Suggestions

To fully comply with the `test-before-setup` rule, the `_async_update_data` methods in both `AdaxCloudCoordinator` and `AdaxLocalCoordinator` should be updated to catch specific exceptions from their respective client libraries (`adax` and `adax_local`) and translate them into the appropriate Home Assistant config entry exceptions.

1.  **Identify Library Exceptions:**
    Determine which exceptions the `adax` and `adax_local` libraries raise for different error conditions:
    *   Authentication failures (e.g., invalid token, wrong password).
    *   Permanent non-auth errors (e.g., account disabled, device incompatible/misconfigured).
    *   Temporary errors (e.g., network connection timeouts, service temporarily unavailable).
    If the libraries do not provide granular exceptions, consider contributing to these libraries to add them.

2.  **Modify `AdaxCloudCoordinator._async_update_data`:**
    Wrap the call to `self.adax_data_handler.get_rooms()` in a `try...except` block.

    ```python
    # In homeassistant/components/adax/coordinator.py
    # (Requires importing relevant exceptions from adax library and Home Assistant)
    # from adax import AdaxAuthException, AdaxFatalException, AdaxConnectionException # Hypothetical exceptions
    # from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
    # from homeassistant.helpers.update_coordinator import UpdateFailed

    class AdaxCloudCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
        # ...
        async def _async_update_data(self) -> dict[str, dict[str, Any]]:
            """Fetch data from the Adax."""
            try:
                rooms = await self.adax_data_handler.get_rooms()
                if rooms is None: # Or however the library indicates no data/error
                    # This might be an UpdateFailed or ConfigEntryError depending on context
                    raise UpdateFailed("Failed to retrieve rooms, API returned no data.")
                return {r["id"]: r for r in rooms}
            except adax.AdaxAuthException as ex:  # Replace with actual auth exception from adax library
                raise ConfigEntryAuthFailed("Adax cloud authentication failed") from ex
            except adax.AdaxAccountClosedException as ex: # Replace with actual permanent error exception
                raise ConfigEntryError("Adax cloud account issue or permanent error") from ex
            except adax.AdaxConnectionException as ex: # For temporary connection issues
                raise UpdateFailed(f"Connection error with Adax cloud: {ex}") from ex
            except Exception as ex: # Catch any other library-specific or unexpected errors
                # Decide if this is an UpdateFailed or ConfigEntryError
                _LOGGER.error("Unexpected error fetching Adax cloud data: %s", ex)
                raise UpdateFailed(f"Unexpected error: {ex}") from ex
    ```

3.  **Modify `AdaxLocalCoordinator._async_update_data`:**
    Wrap the call to `self.adax_data_handler.get_status()` in a `try...except` block.

    ```python
    # In homeassistant/components/adax/coordinator.py
    # (Requires importing relevant exceptions from adax_local library and Home Assistant)
    # from adax_local import AdaxLocalAuthException, AdaxLocalFatalException, AdaxLocalConnectionException # Hypothetical
    # from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
    # from homeassistant.helpers.update_coordinator import UpdateFailed

    class AdaxLocalCoordinator(DataUpdateCoordinator[dict[str, Any] | None]):
        # ...
        async def _async_update_data(self) -> dict[str, Any]:
            """Fetch data from the Adax."""
            try:
                result = await self.adax_data_handler.get_status()
                if result:
                    return cast(dict[str, Any], result)
                # If get_status() returns a falsy value that indicates a problem:
                raise UpdateFailed("Got invalid or empty status from local Adax device")
            except adax_local.AdaxLocalInvalidTokenException as ex:  # Replace with actual auth exception
                raise ConfigEntryAuthFailed("Invalid token for local Adax device") from ex
            except adax_local.AdaxLocalDevicePermanentErrorException as ex: # Replace with actual permanent error
                raise ConfigEntryError("Local Adax device reported a permanent error") from ex
            except adax_local.AdaxLocalConnectionException as ex: # For temporary connection issues
                raise UpdateFailed(f"Connection error with local Adax device: {ex}") from ex
            except Exception as ex: # Catch any other library-specific or unexpected errors
                _LOGGER.error("Unexpected error fetching Adax local data: %s", ex)
                raise UpdateFailed(f"Unexpected error: {ex}") from ex
    ```

**Why these changes satisfy the rule:**

*   By catching specific library exceptions within `_async_update_data` and re-raising them as `ConfigEntryAuthFailed` or `ConfigEntryError`, the integration provides more accurate feedback to the user during setup.
*   `ConfigEntryAuthFailed` allows Home Assistant to trigger a re-authentication flow if one is implemented for the integration.
*   `ConfigEntryError` signals a more permanent issue that likely requires user intervention beyond re-entering credentials.
*   Temporary issues, caught and re-raised as `UpdateFailed` (or if library connection exceptions are directly raised and then wrapped by the base coordinator's `async_refresh` into `UpdateFailed`), will correctly result in `ConfigEntryNotReady` due to the existing `await coordinator.async_config_entry_first_refresh()` call.

These changes ensure that the integration correctly handles various setup failure scenarios as prescribed by the `test-before-setup` rule, improving the user experience by providing clearer and more actionable error information.

_Created at 2025-05-14 15:09:33. Prompt tokens: 6712, Output tokens: 2314, Total tokens: 14843_
