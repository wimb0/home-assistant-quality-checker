# evohome: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `reauthentication-flow` rule requires that integrations using authentication provide a UI flow for users to re-enter their credentials if they become invalid, without needing to delete and re-add the integration. This is typically triggered when an API call fails due to an authentication error.

The `evohome` integration uses username/password authentication and thus this rule applies.

The integration **partially** follows the rule:
1.  **UI Flow Defined:** The `config_flow.py` file correctly defines the necessary steps for reauthentication:
    *   `async_step_reauth(self, entry_data: Mapping[str, Any])`: This method is present and correctly initiates the reauth process by calling `async_step_reauth_confirm`. It receives the existing `entry_data`.
    *   `async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None)`: This method presents a form to the user to input a new password. It then calls `_test_credentials` to validate the new password with the existing username.
    *   If validation is successful, `_update_or_create_entry()` is called, which correctly uses `self.async_update_reload_and_abort(...)` to update the config entry with the new credentials.

2.  **Triggering Mechanism Missing/Incorrect:** The primary issue is that the `EvoDataUpdateCoordinator` in `coordinator.py` does not properly trigger this reauthentication flow when an authentication error occurs during ongoing operations or initial setup after a Home Assistant restart.
    *   In `EvoDataUpdateCoordinator._async_setup()` (called during initial setup):
        ```python
        # homeassistant/components/evohome/coordinator.py
        async def _async_setup(self) -> None:
            # ...
            try:
                await self.client.update(dont_update_status=True)  # only config for now
            except ec2.EvohomeError as err: # Catches generic EvohomeError
                raise UpdateFailed(err) from err
            # ...
        ```
        If `self.client.update()` (which uses `evohomeasync2`) fails due to `ec2.BadUserCredentialsError` or a relevant `ec2.AuthenticationFailedError`, it's caught by the generic `ec2.EvohomeError` handler and re-raised as `UpdateFailed`. This does not trigger the reauth flow; `ConfigEntryAuthFailed` should be raised instead.

    *   In `EvoDataUpdateCoordinator._update_v2_api_state()` (called during regular updates):
        ```python
        # homeassistant/components/evohome/coordinator.py
        async def _update_v2_api_state(self, *args: Any) -> None:
            # ...
            try:
                status = await self.loc.update()
            # ...
            except ec2.EvohomeError as err: # Catches generic EvohomeError
                raise UpdateFailed(err) from err
        ```
        Similar to `_async_setup`, authentication errors from `self.loc.update()` are caught as generic `ec2.EvohomeError` and result in `UpdateFailed`, not `ConfigEntryAuthFailed`.

    *   In `EvoDataUpdateCoordinator._update_v1_api_temps()` (if high precision is enabled):
        ```python
        # homeassistant/components/evohome/coordinator.py
        async def _update_v1_api_temps(self) -> None:
            # ...
            except ec1.BadUserCredentialsError as err: # Uses evohomeasync (v1)
                self.logger.warning(
                    (
                        "Unable to obtain high-precision temperatures. "
                        "The feature will be disabled until next restart: %r"
                    ),
                    err,
                )
                self.client_v1 = None
            # ...
        ```
        Here, `ec1.BadUserCredentialsError` from the older `evohomeasync` library results in a warning and disabling the feature, rather than triggering a reauth flow by raising `ConfigEntryAuthFailed`.

Because these specific authentication errors are not translated into `ConfigEntryAuthFailed` by the coordinator, Home Assistant's core machinery (`DataUpdateCoordinator._async_refresh` which calls `self.async_config_entry_retry_setup(err)` upon `ConfigEntryAuthFailed`) is not invoked to start the reauthentication process. The user would experience failed updates without being prompted to correct their credentials.

## Suggestions

To make the `evohome` integration fully compliant with the `reauthentication-flow` rule, the `EvoDataUpdateCoordinator` needs to be modified to detect specific authentication errors from the underlying `evohomeasync2` and `evohomeasync` libraries and raise `homeassistant.exceptions.ConfigEntryAuthFailed`.

1.  **Modify `EvoDataUpdateCoordinator._async_setup()`:**
    Catch specific authentication exceptions from `evohomeasync2` and raise `ConfigEntryAuthFailed`.
    ```python
    # homeassistant/components/evohome/coordinator.py
    from homeassistant.exceptions import ConfigEntryAuthFailed # Add this import

    # ... inside EvoDataUpdateCoordinator class ...
    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            await self.client.update(dont_update_status=True)  # only config for now
        except ec2.BadUserCredentialsError as err:
            raise ConfigEntryAuthFailed("Invalid credentials during setup") from err
        except ec2.AuthenticationFailedError as err:
            # Potentially check err.status if it can distinguish auth errors from others
            raise ConfigEntryAuthFailed(f"Authentication failed during setup: {err}") from err
        except ec2.EvohomeError as err: # Catch other client errors as UpdateFailed
            raise UpdateFailed(f"Failed to setup evohome client: {err}") from err
        # ... rest of the method ...
    ```

2.  **Modify `EvoDataUpdateCoordinator._update_v2_api_state()`:**
    Similarly, handle authentication errors during runtime updates.
    ```python
    # homeassistant/components/evohome/coordinator.py
    # ... inside EvoDataUpdateCoordinator class ...
    async def _update_v2_api_state(self, *args: Any) -> None:
        """Get the latest modes, temperatures, setpoints of a Location."""
        try:
            status = await self.loc.update()
        except ec2.BadUserCredentialsError as err:
            raise ConfigEntryAuthFailed("Invalid credentials during update") from err
        except ec2.AuthenticationFailedError as err:
            # Potentially check err.status
            raise ConfigEntryAuthFailed(f"Authentication failed during update: {err}") from err
        except ec2.ApiRequestFailedError as err:
            if err.status != HTTPStatus.TOO_MANY_REQUESTS:
                raise UpdateFailed(err) from err
            raise UpdateFailed(
                f"""
                    The vendor's API rate limit has been exceeded.
                    Consider increasing the {CONF_SCAN_INTERVAL}
                """
            ) from err
        except ec2.EvohomeError as err:
            raise UpdateFailed(err) from err
        # ... rest of the method ...
    ```

3.  **Modify `EvoDataUpdateCoordinator._update_v1_api_temps()`:**
    If `client_v1` (high precision) is active, ensure its authentication errors also trigger reauth.
    ```python
    # homeassistant/components/evohome/coordinator.py
    # ... inside EvoDataUpdateCoordinator class ...
    async def _update_v1_api_temps(self) -> None:
        """Get the latest high-precision temperatures of the default Location."""
        assert self.client_v1 is not None  # mypy check
        try:
            await self.client_v1.update()
        except ec1.BadUserCredentialsError as err: # From evohomeasync v1
            # Instead of just logging and disabling:
            raise ConfigEntryAuthFailed("Invalid v1 API credentials for high-precision temps") from err
        except ec1.EvohomeError as err:
            self.logger.warning(
                (
                    "Unable to obtain the latest high-precision temperatures. "
                    "They will be ignored this refresh cycle: %r"
                ),
                err,
            )
            self.temps = {}
        else:
            self.temps = await self.client_v1.location_by_id[
                self.loc.id
            ].get_temperatures(dont_update_status=True)
        self.logger.debug("Status (high-res temps) = %s", self.temps)
    ```

By implementing these changes, when the Evohome service reports an authentication issue, the `EvoDataUpdateCoordinator` will raise `ConfigEntryAuthFailed`. Home Assistant will then catch this exception and automatically initiate the reauthentication flow that is already defined in `config_flow.py`, prompting the user to update their credentials. This will make the integration fully compliant with the `reauthentication-flow` rule.

---

_Created at 2025-05-29 12:48:45. Prompt tokens: 22349, Output tokens: 2203, Total tokens: 30139._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
