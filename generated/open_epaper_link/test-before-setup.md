# open_epaper_link: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires that integrations check during their initialization (`async_setup_entry`) if they can be set up correctly and raise specific Home Assistant exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) upon failure. This provides immediate and clear feedback to the user.

This rule applies to the `open_epaper_link` integration as it implements `async_setup_entry` to connect to an external hub (the OpenEPaperLink AP).

The integration currently does **not** fully follow this rule. While it performs initial setup steps, failures in these steps or in establishing the critical WebSocket connection do not consistently result in the required Home Assistant exceptions being raised from `async_setup_entry`.

**Key areas of non-compliance:**

1.  **`hub.async_setup_initial()` failures:**
    *   In `homeassistant/components/open_epaper_link/__init__.py`, the `async_setup_entry` function calls `hub.async_setup_initial()`.
        ```python
        # __init__.py
        async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
            hub = Hub(hass, entry)

            # Do basic setup without WebSocket connection
            if not await hub.async_setup_initial(): # <--- Problem here
                return False
            # ...
            return True
        ```
    *   The `hub.async_setup_initial()` method (in `homeassistant/components/open_epaper_link/hub.py`) attempts to fetch AP information (`self.async_update_ap_info()`) and load all tags (`self.async_load_all_tags()`). These methods involve HTTP requests.
    *   If these HTTP requests fail (e.g., AP is offline, timeout, network error), `async_setup_initial()` catches the exceptions, logs a warning/error, and returns `False`.
        ```python
        # hub.py - in async_setup_initial()
        try:
            await self.async_update_ap_info() # Can fail
        except Exception as err:
            _LOGGER.warning("Could not load initial AP info: %s", str(err)) # Logs, but doesn't raise HA exception

        try:
            await self.async_load_all_tags() # Can fail
        except Exception as err:
            _LOGGER.warning("Could not load initial tags from AP: %s", str(err)) # Logs, but doesn't raise HA exception
        return True # if individual calls log and don't re-raise to this level

        # Outer try-except in async_setup_initial()
        except Exception as err:
            _LOGGER.error("Failed to set up hub: %s", err)
            return False # Returns False instead of raising ConfigEntryNotReady/ConfigEntryError
        ```
    *   When `hub.async_setup_initial()` returns `False`, `async_setup_entry` also returns `False`. This is a "silent" failure from Home Assistant's perspective. It should instead raise `ConfigEntryNotReady` for temporary issues (like connection errors) or `ConfigEntryError` for more permanent setup problems.

2.  **`hub.async_start_websocket()` failures during initial setup:**
    *   In `__init__.py`, if Home Assistant is already running (`hass.is_running`), `async_setup_entry` directly calls `await hub.async_start_websocket()`.
        ```python
        # __init__.py
        if hass.is_running:
            # If HA is already running, start WebSocket immediately
            await hub.async_start_websocket() # <--- Problem here
        else:
            # Otherwise wait for the started event
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_websocket)

        return True
        ```
    *   The `hub.async_start_websocket()` method (in `hub.py`) attempts to establish the WebSocket connection. If it fails (e.g., timeout, connection refused), it logs an error and returns `False`.
        ```python
        # hub.py - in async_start_websocket()
        try:
            async with async_timeout.timeout(CONNECTION_TIMEOUT):
                # ... connection attempt ...
                if not self.online: # if connection failed
                    _LOGGER.error("Failed to establish WebSocket connection")
                    return False # Returns False instead of raising ConfigEntryNotReady
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout while establishing WebSocket connection")
            return False # Returns False instead of raising ConfigEntryNotReady
        ```
    *   Crucially, `async_setup_entry` does **not** check the return value of `await hub.async_start_websocket()`. This means if the WebSocket connection fails during this initial attempt, `async_setup_entry` will still proceed and return `True`, indicating a successful setup to Home Assistant, even though a critical component is not functional. This should raise `ConfigEntryNotReady`.

The integration does not use a `DataUpdateCoordinator` with `async_config_entry_first_refresh()` for its primary setup, so the implicit implementation note from the rule does not apply here.

## Suggestions

To make the `open_epaper_link` integration compliant with the `test-before-setup` rule, the following changes are recommended:

1.  **Modify `Hub` methods to raise exceptions on failure:**
    *   Update `hub.py`: `async_setup_initial`, `async_update_ap_info`, `_fetch_all_tags_from_ap`, and `async_start_websocket` should raise specific custom exceptions (e.g., `APConnectionError`, `APSetupError`, inheriting from `HomeAssistantError`) or allow standard exceptions like `aiohttp.ClientError` and `asyncio.TimeoutError` to propagate, instead of returning `False` or only logging errors.

    *   **Example for `hub.async_update_ap_info()`:**
        ```python
        # homeassistant/components/open_epaper_link/hub.py

        # Define custom exceptions (can be at the top of hub.py or in a new errors.py)
        from homeassistant.exceptions import HomeAssistantError

        class APConnectionError(HomeAssistantError):
            """Error to indicate an AP connection error."""

        class APError(HomeAssistantError):
            """Error to indicate a generic AP setup error."""

        # ...

        async def async_update_ap_info(self) -> None: # Should not return, but raise on error
            """Force update of AP configuration."""
            try:
                async with async_timeout.timeout(10): # Or CONNECTION_TIMEOUT
                    async with self._session.get(f"http://{self.host}/sysinfo") as response:
                        response.raise_for_status() # Raises aiohttp.ClientResponseError for 4xx/5xx
                        data = await response.json()
                        self.ap_env = data.get("env")
                        self.ap_model = self._format_ap_model(self.ap_env)
            except asyncio.TimeoutError as ex:
                _LOGGER.debug("Timeout fetching AP sysinfo for %s: %s", self.host, ex)
                raise APConnectionError(f"Timeout fetching AP sysinfo from {self.host}") from ex
            except aiohttp.ClientError as ex:
                _LOGGER.debug("ClientError fetching AP sysinfo for %s: %s", self.host, ex)
                raise APConnectionError(f"Error connecting to AP at {self.host} to fetch sysinfo: {ex}") from ex
            except Exception as ex: # Catch JSON decode errors or other unexpected issues
                _LOGGER.error("Failed to process AP sysinfo for %s: %s", self.host, ex)
                raise APError(f"Error processing AP sysinfo from {self.host}: {ex}") from ex
        ```
    *   Apply similar error handling to `_fetch_all_tags_from_ap()` and `async_start_websocket()`. `async_setup_initial()` should then let these exceptions propagate upwards.

2.  **Modify `async_setup_entry` in `__init__.py` to handle exceptions:**
    *   Wrap the calls to `hub.async_setup_initial()` and `hub.async_start_websocket()` (when `hass.is_running`) in `try...except` blocks.
    *   These blocks should catch the exceptions raised by the `Hub` methods (or standard `aiohttp` exceptions) and re-raise them as `ConfigEntryNotReady` for connection/timeout issues, or `ConfigEntryError` for other setup failures.

    *   **Example for `__init__.py`:**
        ```python
        # homeassistant/components/open_epaper_link/__init__.py
        import aiohttp # Add if not already imported
        import asyncio # Add if not already imported
        from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryError
        from .hub import APConnectionError, APError # Import custom exceptions

        # ...

        async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
            hub = Hub(hass, entry)

            try:
                # Do basic setup without WebSocket connection
                await hub.async_setup_initial()
            except (APConnectionError, aiohttp.ClientError, asyncio.TimeoutError) as ex:
                raise ConfigEntryNotReady(f"Failed to connect to OpenEPaperLink AP at {hub.host} during initial setup: {ex}") from ex
            except APError as ex:
                raise ConfigEntryError(f"Failed to complete initial setup for OpenEPaperLink AP at {hub.host}: {ex}") from ex
            # Catch any other unexpected errors during this critical phase
            except Exception as ex:
                _LOGGER.exception("Unexpected error during OpenEPaperLink initial setup for %s", hub.host)
                raise ConfigEntryError(f"An unexpected error occurred during OpenEPaperLink setup: {ex}") from ex


            hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
            await async_setup_services(hass)
            entry.async_on_unload(entry.add_update_listener(async_update_options))

            async def start_websocket_task(_event=None):
                """Start WebSocket connection task, handling potential initial failures."""
                try:
                    # async_start_websocket should be modified to raise exceptions instead of returning bool
                    await hub.async_start_websocket()
                except (APConnectionError, aiohttp.ClientError, asyncio.TimeoutError) as ex:
                    # If this happens during initial setup (hass.is_running), it needs to be handled.
                    # If it happens post-setup (EVENT_HOMEASSISTANT_STARTED), the hub's internal retry is fine.
                    # This specific re-raise is for the hass.is_running case.
                    _LOGGER.warning("Initial WebSocket connection to %s failed: %s. Will retry.", hub.host, ex)
                    if hass.is_running and not hub.online : # Check if it's part of initial setup.
                         raise ConfigEntryNotReady(f"WebSocket connection to {hub.host} failed during setup: {ex}") from ex
                    # If not hass.is_running, the hub's internal retry logic will handle it.
                except APError as ex:
                    if hass.is_running and not hub.online:
                        raise ConfigEntryError(f"Error during WebSocket startup for {hub.host}: {ex}") from ex
                except Exception as ex:
                    if hass.is_running and not hub.online:
                        _LOGGER.exception("Unexpected error during WebSocket startup for %s", hub.host)
                        raise ConfigEntryError(f"An unexpected error occurred during WebSocket startup: {ex}") from ex


            if hass.is_running:
                # If HA is already running, try to start WebSocket immediately as part of setup.
                # Failure here should prevent setup from completing successfully.
                await start_websocket_task()
            else:
                # Otherwise wait for the started event. Failures here are post-setup.
                # The hub's internal _websocket_handler should manage retries.
                hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_websocket_task)

            return True
        ```

**Reasoning for these changes:**

*   By raising `ConfigEntryNotReady`, Home Assistant will automatically retry setting up the integration later, which is appropriate for temporary network issues or if the AP is temporarily offline.
*   By raising `ConfigEntryError`, Home Assistant will mark the setup as failed and inform the user, which is appropriate for configuration issues or persistent problems that are unlikely to resolve on their own.
*   This provides a much better user experience by giving clear feedback on setup failures rather than the integration failing silently or appearing to work when critical parts are non-functional.

_Created at 2025-05-14 20:41:20. Prompt tokens: 60541, Output tokens: 3097, Total tokens: 69530_
