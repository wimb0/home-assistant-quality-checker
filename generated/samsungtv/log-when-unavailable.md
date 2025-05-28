```markdown
# samsungtv: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `log-when-unavailable` rule requires integrations to log at `info` level when a device or service becomes unavailable, and again when it becomes available, logging each transition only once to avoid spamming the logs. This rule is applicable to the `samsungtv` integration as it interacts with an external device (the TV) that can become unavailable due to various reasons (e.g., network issues, being powered off).

The `samsungtv` integration uses a `DataUpdateCoordinator` (`SamsungTVDataUpdateCoordinator` in `coordinator.py`). The standard pattern for coordinators to comply with this rule is to raise `UpdateFailed` within the `_async_update_data` method when the device/service is unavailable. The `DataUpdateCoordinator` base class then handles the required logging (once when transitioning to unavailable, once when transitioning back to available, both at `info` level).

Looking at `homeassistant/components/samsungtv/coordinator.py`, the `_async_update_data` method fetches the device's power state using `await self.bridge.async_is_on()`. It then updates the `self.is_on` attribute based on the result.

```python
# homeassistant/components/samsungtv/coordinator.py
# ...
class SamsungTVDataUpdateCoordinator(DataUpdateCoordinator[None]):
    # ...
    async def _async_update_data(self) -> None:
        """Fetch data from SamsungTV bridge."""
        if self.bridge.auth_failed:
            return
        old_state = self.is_on
        if self.bridge.power_off_in_progress:
            self.is_on = False
        else:
            self.is_on = await self.bridge.async_is_on()
        if self.is_on != old_state:
            LOGGER.debug("TV %s state updated to %s", self.bridge.host, self.is_on)

        if self.async_extra_update:
            await self.async_extra_update()
```

The `_async_update_data` method in `samsungtv` does *not* raise `UpdateFailed` when the device is detected as off or unreachable. Instead, it sets `self.is_on` to `False`. While the coordinator base class handles logging when `UpdateFailed` is raised, it does *not* automatically log availability transitions when the `_async_update_data` method completes successfully but determines the device is off (by setting an internal state like `self.is_on`).

The existing code logs a debug message (`LOGGER.debug("TV %s state updated to %s", self.bridge.host, self.is_on)`) when the `is_on` state changes. This is helpful, but it is at the `debug` level, not the required `info` level, and doesn't explicitly state *why* it became unavailable (e.g., connection error).

Therefore, the integration does not fully comply with the rule's requirement to log availability transitions at the `info` level.

## Suggestions

To comply with the `log-when-unavailable` rule, the `SamsungTVDataUpdateCoordinator` should be modified to log the availability transitions explicitly at the `info` level. Since the coordinator determines availability internally rather than relying on `UpdateFailed`, it needs to implement the tracking of availability state and corresponding logging logic itself, similar to the entity example provided in the rule description, but within the coordinator's `_async_update_data` method.

Here's how the `_async_update_data` method could be modified:

```python
# homeassistant/components/samsungtv/coordinator.py

# ... imports and class definition ...

class SamsungTVDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Coordinator for the SamsungTV integration."""

    config_entry: SamsungTVConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SamsungTVConfigEntry,
        bridge: SamsungTVBridge,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

        self.bridge = bridge
        self.is_on: bool | None = False
        self.async_extra_update: Callable[[], Coroutine[Any, Any, None]] | None = None
        # Add an attribute to track if unavailability has been logged
        self._unavailable_logged: bool = False

    async def _async_update_data(self) -> None:
        """Fetch data from SamsungTV bridge."""
        if self.bridge.auth_failed:
            # Auth failed means device is effectively unavailable
            if not self._unavailable_logged:
                LOGGER.info("TV %s is unavailable due to authentication failure", self.bridge.host)
                self._unavailable_logged = True
            self.is_on = False # Ensure state is reflected
            # Do not return here if you want to allow re-auth attempts to connect
            # If returning, make sure the coordinator does not try to update platforms
            # when bridge.auth_failed is true. The current code avoids this.
            return

        old_state = self.is_on
        
        try:
            if self.bridge.power_off_in_progress:
                self.is_on = False
            else:
                self.is_on = await self.bridge.async_is_on()
            
            # Check if the device is on and if it was previously unavailable
            if self.is_on and self._unavailable_logged:
                LOGGER.info("TV %s is back online", self.bridge.host)
                self._unavailable_logged = False

        except Exception as ex:
             # Catch potential exceptions during async_is_on (less likely with current bridge impl, but good practice)
             # This would indicate a connection issue
             self.is_on = False
             if not self._unavailable_logged:
                # Use exception detail if available, otherwise a generic message
                log_message = f"TV {self.bridge.host} is unavailable"
                if ex:
                    log_message += f": {ex}"
                LOGGER.info(log_message)
                self._unavailable_logged = True
             # The base DataUpdateCoordinator will log the exception separately at error level

        # Optional: Log state changes at debug level if still desired
        # if self.is_on != old_state and self._unavailable_logged is (not self.is_on):
        #     LOGGER.debug("TV %s state updated to %s", self.bridge.host, self.is_on)


        if self.async_extra_update:
            await self.async_extra_update()

```

This modified code:

1.  Introduces a `_unavailable_logged` boolean flag to track whether the unavailability log message has been sent.
2.  Logs at `info` level when `self.is_on` transitions from `True` to `False` and `_unavailable_logged` is `False`.
3.  Logs at `info` level when `self.is_on` transitions from `False` to `True` and `_unavailable_logged` is `True`.
4.  Handles the `auth_failed` case similarly, as authentication failure implies unavailability.
5.  Ensures logging only happens once per transition state by using the `_unavailable_logged` flag.

This approach aligns with the spirit of the rule and provides helpful `info` level messages to the user without spamming the logs.

Alternatively, restructure `_async_update_data` to raise `UpdateFailed` whenever the TV cannot be reached or is off, allowing the base `DataUpdateCoordinator` to handle the logging automatically. This would involve modifying the bridge methods (`async_is_on`, etc.) to raise exceptions when communication fails or the TV is off, and catching these exceptions in `_async_update_data` to raise `UpdateFailed`. Given the current bridge implementation's internal error handling and the use of `async_is_on`, implementing the explicit logging within the coordinator's `_async_update_data` as suggested above might be a more straightforward path without major refactoring of the bridge classes.

```python
# Alternative approach: Raise UpdateFailed in coordinator

# homeassistant/components/samsungtv/coordinator.py

# ... imports and class definition ...

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

class SamsungTVDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Coordinator for the SamsungTV integration."""

    config_entry: SamsungTVConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SamsungTVConfigEntry,
        bridge: SamsungTVBridge,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

        self.bridge = bridge
        # We no longer need to track is_on explicitly here, the coordinator base handles availability
        self.async_extra_update: Callable[[], Coroutine[Any, Any, None]] | None = None

    async def _async_update_data(self) -> None:
        """Fetch data from SamsungTV bridge."""
        if self.bridge.auth_failed:
            # Raising UpdateFailed will make the coordinator mark the device unavailable
            # The base coordinator will handle the logging "Update of X failed"
            # This covers the auth failed case as unavailability, but the log message
            # might not be as specific as "authentication failure".
            raise UpdateFailed("Authentication failed")

        try:
            # Need to check power_off_in_progress first as async_is_on might still return True
            # briefly after sending power off. Or modify async_is_on to respect this state.
            if self.bridge.power_off_in_progress:
                 raise UpdateFailed("TV is powering off") # Mark unavailable while powering off

            # Modify async_is_on in bridge.py to raise exceptions (e.g., ConnectionError)
            # when communication fails or device is unreachable, rather than just returning False.
            is_on = await self.bridge.async_is_on()
            if not is_on:
                raise UpdateFailed("TV is off or unreachable")

        except Exception as ex:
             # Catch any exceptions from bridge methods and re-raise as UpdateFailed
             # The base coordinator handles the logging of the failure and the unavailable state
             raise UpdateFailed(f"Failed to communicate with TV: {ex}") from ex

        # If we reach here, the TV is on and reachable.
        # The base coordinator will mark it available if it was previously unavailable
        # and log "Update for X was successful" (which might not be the desired "back online" message)

        if self.async_extra_update:
            await self.async_extra_update()

```
This alternative approach requires significant changes to the bridge classes to ensure `async_is_on` and other communication methods raise appropriate exceptions instead of just returning `False` or handling errors internally with debug logs. The first suggestion, handling the logging explicitly within the coordinator based on `self.is_on` state changes, is likely simpler to implement with the current structure.

Choose the approach that best fits the integration's architecture, but the explicit logging within the coordinator's `_async_update_data` method seems more aligned with how this specific coordinator already determines availability.

```

_Created at 2025-05-25 11:30:30. Prompt tokens: 30425, Output tokens: 2736, Total tokens: 34337_
