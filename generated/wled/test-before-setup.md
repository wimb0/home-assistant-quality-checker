# wled: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires that integrations check if they can be set up correctly during initialization and raise specific exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) upon failure. This can also be achieved implicitly using a data update coordinator's `async_config_entry_first_refresh()` method.

This rule applies to the `wled` integration as it communicates with an external device and needs to ensure connectivity and basic functionality during setup.

The `wled` integration **follows** this rule. Here's how:

1.  In `__init__.py`, the `async_setup_entry` function initializes the `WLEDDataUpdateCoordinator` and then calls `await entry.runtime_data.async_config_entry_first_refresh()`.
    ```python
    # __init__.py
    async def async_setup_entry(hass: HomeAssistant, entry: WLEDConfigEntry) -> bool:
        """Set up WLED from a config entry."""
        entry.runtime_data = WLEDDataUpdateCoordinator(hass, entry=entry)
        await entry.runtime_data.async_config_entry_first_refresh() # Key call

        # Set up all platforms for this device/entry.
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # ...
        return True
    ```

2.  The `WLEDDataUpdateCoordinator` (in `coordinator.py`) implements the `_async_update_data` method, which attempts to fetch data from the WLED device using `await self.wled.update()`.
    ```python
    # coordinator.py
    class WLEDDataUpdateCoordinator(DataUpdateCoordinator[WLEDDevice]):
        # ...
        async def _async_update_data(self) -> WLEDDevice:
            """Fetch data from WLED."""
            try:
                device = await self.wled.update()
            except WLEDError as error: # Catches errors from the wled library
                raise UpdateFailed(f"Invalid response from API: {error}") from error

            # ...
            return device
    ```

3.  If `self.wled.update()` raises a `WLEDError` (e.g., due to the device being offline, unreachable, or returning an invalid response), the coordinator catches this exception and raises `UpdateFailed`.

4.  The `DataUpdateCoordinator` base class, when `async_config_entry_first_refresh()` is called, handles an `UpdateFailed` exception by re-raising it as `ConfigEntryNotReady`. This is standard behavior for coordinators.

This mechanism fulfills the rule's requirements:
*   A check is performed during initialization (`async_config_entry_first_refresh`).
*   If the check fails (e.g., WLED device is offline), `ConfigEntryNotReady` is raised. This informs Home Assistant that the setup failed temporarily and should be retried, providing immediate feedback to the user via the UI (entry shows a retry state) and logs.

The rule's documentation explicitly states:
> Please note that this may also be implemented implicitly when using a data update coordinator via `await coordinator.async_config_entry_first_refresh()`.

The `wled` integration uses this exact pattern. While it doesn't differentiate between various `WLEDError` types to raise `ConfigEntryError` for potentially permanent issues (as WLED API doesn't involve authentication, `ConfigEntryAuthFailed` is not applicable for device communication), raising `ConfigEntryNotReady` for general device communication/API errors is an appropriate and compliant approach according to the rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:30:51. Prompt tokens: 21523, Output tokens: 934, Total tokens: 27274_
