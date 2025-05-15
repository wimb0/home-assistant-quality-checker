# open_epaper_link: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `action-exceptions` rule requires that service actions raise specific Home Assistant exceptions (`ServiceValidationError` for incorrect usage or `HomeAssistantError` for other failures) when they encounter problems. This ensures users are properly informed about issues through the UI.

This rule applies to the `open_epaper_link` integration as it registers multiple services (e.g., `drawcustom`, `setled`, `reboot_tag`) that interact with external hardware (the OpenEPaperLink AP and associated tags) and process user-provided data. These interactions are prone to failures such as network errors, device unavailability, or invalid input.

The integration currently does NOT fully follow this rule. While some services and helper functions correctly raise `HomeAssistantError` (e.g., `drawcustom_service` for initial AP offline check, `upload_image` for upload failures, `get_hub`), several key areas exhibit shortcomings:

1.  **Incorrect Exception Type**:
    *   The `get_entity_id_from_device_id` function (used by many services) raises `HomeAssistantError` for issues like "device not found." According to the rule, such errors (referencing something that doesn't exist) should raise `ServiceValidationError`.

2.  **Failures Not Raising Exceptions**:
    *   `setled_service`: If the HTTP request to set the LED pattern fails (e.g., network error, AP returns non-200 status), it only logs a warning and does not raise any exception. The `requests.get` call is also not wrapped in a `try...except` block to handle potential `requests.exceptions.RequestException` or timeouts.
        ```python
        # homeassistant/components/open_epaper_link/services.py
        # In setled_service:
        result = await hass.async_add_executor_job(requests.get, url)
        if result.status_code != 200:
            _LOGGER.warning("LED pattern update failed with status code: %s", result.status_code)
        ```
    *   Helper functions in `util.py` (`send_tag_cmd`, `reboot_ap`) return `False` and log errors instead of raising exceptions. This affects services that rely on them:
        *   `clear_pending_service`, `force_refresh_service`, `reboot_tag_service`, `scan_channels_service` (all use `send_tag_cmd`).
        *   `reboot_ap_service` (uses `reboot_ap`).
        These services will silently fail from the user's perspective if the underlying utility functions encounter issues.
        ```python
        # homeassistant/components/open_epaper_link/util.py
        # In send_tag_cmd:
        # ...
        # except Exception as e:
        #     _LOGGER.error("Failed to send %s command to %s: %s", cmd, entity_id, str(e))
        #     return False # Should raise HomeAssistantError
        ```
    *   `refresh_tag_types_service`: This service relies on `TagTypesManager.ensure_types_loaded()`. If the underlying `_fetch_tag_types()` method in `tag_types.py` fails to fetch data from GitHub, it catches the generic `Exception`, logs an error, and may use fallback data. It does not raise an exception that would propagate to `refresh_tag_types_service` to inform the user that the refresh operation failed.
        ```python
        # homeassistant/components/open_epaper_link/tag_types.py
        # In TagTypesManager._fetch_tag_types:
        # except Exception as e:
        #     _LOGGER.error(f"Error fetching tag types: {str(e)}")
        #     if not self._tag_types:
        #         self._load_fallback_types() # Silently uses fallback
        #         await self.save_to_storage()
        ```

3.  **Background Task Failures Not Propagated**:
    *   In `drawcustom_service`, image uploads are queued using `UploadQueueHandler` and executed in background tasks. If an `upload_image` task fails (e.g., network error during upload), `UploadQueueHandler._process_queue` catches the exception and logs it. However, the `drawcustom_service` call itself would have already returned successfully to the user by just queueing the task. The failure of the actual upload is not reported back as an exception from the originating service call.

## Suggestions

To make the `open_epaper_link` integration compliant with the `action-exceptions` rule, the following changes are recommended:

1.  **Use `ServiceValidationError` for Invalid References in `get_entity_id_from_device_id`**:
    Modify `get_entity_id_from_device_id` in `services.py` to raise `ServiceValidationError` when a device is not found or is not an OpenEPaperLink device, as this represents incorrect input/reference.
    ```python
    from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

    # ... inside get_entity_id_from_device_id
    if not device:
        raise ServiceValidationError(f"Device {device_id} not found. It may not be a valid OpenEPaperLink device or is not yet discovered.")
    # ...
    if domain_mac[0] != DOMAIN:
        raise ServiceValidationError(f"Device {device_id} is not an OpenEPaperLink device.")
    ```

2.  **Handle Errors and Raise Exceptions in `setled_service`**:
    Wrap the HTTP request in `setled_service` (in `services.py`) with `try...except` blocks and a timeout. Raise `HomeAssistantError` on failures (e.g., non-200 status, timeout, network issues).
    ```python
    # In services.py, inside setled_service
    # Ensure async_timeout and requests.exceptions are imported
    import async_timeout
    import requests.exceptions # If not already present

    # ...
    try:
        async with async_timeout.timeout(15): # Example timeout
            result = await hass.async_add_executor_job(requests.get, url)
        if result.status_code != 200:
            raise HomeAssistantError(
                f"Failed to set LED pattern for tag {mac}. AP returned status: {result.status_code}. Response: {result.text[:100]}"
            )
        _LOGGER.info("Successfully set LED pattern for %s", mac)
    except asyncio.TimeoutError as err:
        raise HomeAssistantError(f"Timeout while setting LED pattern for tag {mac}.") from err
    except requests.exceptions.RequestException as err:
        raise HomeAssistantError(f"Network error setting LED pattern for tag {mac}: {err}") from err
    except Exception as err: # Catch-all for other unexpected errors
        raise HomeAssistantError(f"An unexpected error occurred while setting LED pattern for tag {mac}: {err}") from err
    ```

3.  **Refactor `util.send_tag_cmd` to Raise Exceptions**:
    Modify `send_tag_cmd` in `util.py` to raise `HomeAssistantError` on failure instead of returning `False`. This will allow services like `clear_pending_service` to correctly propagate errors.
    ```python
    # In homeassistant/components/open_epaper_link/util.py
    from homeassistant.exceptions import HomeAssistantError # Add if not present
    import async_timeout # Add for timeout
    import requests.exceptions # Add for specific network exceptions

    async def send_tag_cmd(hass: HomeAssistant, entity_id: str, cmd: str) -> None: # Changed return type
        hub = hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]
        if not hub.online:
            raise HomeAssistantError(f"Cannot send command '{cmd}' to {entity_id}: AP is offline.")

        mac = entity_id.split(".")[1].upper()
        url = f"http://{hub.host}/tag_cmd"
        data = {'mac': mac, 'cmd': cmd}

        try:
            async with async_timeout.timeout(10): # Example timeout
                result = await hass.async_add_executor_job(
                    lambda: requests.post(url, data=data, timeout=5) # Add explicit timeout to requests
                )
            if result.status_code == 200:
                _LOGGER.info("Sent %s command to %s", cmd, entity_id)
            else:
                raise HomeAssistantError(
                    f"Failed to send '{cmd}' command to {entity_id}: AP returned HTTP {result.status_code}. Response: {result.text[:100]}"
                )
        except asyncio.TimeoutError as err:
            raise HomeAssistantError(f"Timeout sending '{cmd}' command to {entity_id}.") from err
        except requests.exceptions.RequestException as err:
            raise HomeAssistantError(f"Network error sending '{cmd}' command to {entity_id}: {err}") from err
        except Exception as e:
            # Ensure it's not a HomeAssistantError already to avoid double wrapping if one was raised internally
            if not isinstance(e, HomeAssistantError):
                raise HomeAssistantError(f"Unexpected error sending '{cmd}' command to {entity_id}: {e}") from e
            else:
                raise # Re-raise if it's already a HomeAssistantError
    ```

4.  **Refactor `util.reboot_ap` to Raise Exceptions**:
    Similarly, modify `reboot_ap` in `util.py` to raise `HomeAssistantError` on failure.
    ```python
    # In homeassistant/components/open_epaper_link/util.py
    # Ensure necessary imports as above

    async def reboot_ap(hass: HomeAssistant) -> None: # Changed return type
        hub = hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]
        if not hub.online:
            raise HomeAssistantError("Cannot reboot AP: AP is offline.")

        url = f"http://{hub.host}/reboot"
        try:
            async with async_timeout.timeout(10): # Example timeout
                result = await hass.async_add_executor_job(
                    lambda: requests.post(url, timeout=5) # Add explicit timeout
                )
            if result.status_code == 200:
                _LOGGER.info("Rebooted OEPL Access Point")
            else:
                raise HomeAssistantError(
                    f"Failed to reboot OEPL Access Point: AP returned HTTP {result.status_code}. Response: {result.text[:100]}"
                )
        except asyncio.TimeoutError as err:
            raise HomeAssistantError("Timeout while trying to reboot AP.") from err
        except requests.exceptions.RequestException as err:
            raise HomeAssistantError(f"Network error while trying to reboot AP: {err}") from err
        except Exception as e:
            if not isinstance(e, HomeAssistantError):
                raise HomeAssistantError(f"Unexpected error while trying to reboot AP: {e}") from e
            else:
                raise
    ```

5.  **Ensure `refresh_tag_types_service` Reports GitHub Fetch Failures**:
    Modify `TagTypesManager._fetch_tag_types` (in `tag_types.py`) to raise `HomeAssistantError` if fetching from GitHub fails, especially when a refresh is forced (i.e., `is_forced_refresh` is true). The `refresh_tag_types_service` in `services.py` should then be prepared to catch and re-raise this.

    *   In `tag_types.py`, `TagTypesManager`:
        Modify `_fetch_tag_types` to accept `is_forced_refresh` and raise an error accordingly:
        ```python
        # In TagTypesManager._fetch_tag_types
        # Add 'is_forced_refresh: bool' parameter
        async def _fetch_tag_types(self, *, is_forced_refresh: bool) -> None:
            try:
                # ... existing fetch logic ...
                if not new_types and is_forced_refresh:
                    raise HomeAssistantError("Failed to fetch any valid tag definitions from GitHub during forced refresh.")
            except Exception as e:
                _LOGGER.error(f"Error fetching tag types: {str(e)}")
                if is_forced_refresh:
                    raise HomeAssistantError(f"Failed to fetch tag types from GitHub: {e}") from e
                if not self._tag_types: # Fallback only if not forced and no types exist
                    self._load_fallback_types()
                    await self.save_to_storage()
        ```
        Adjust `ensure_types_loaded` to pass this flag correctly:
        ```python
        # In TagTypesManager.ensure_types_loaded
        async def ensure_types_loaded(self) -> None:
            async with self._lock:
                # Determine if it's effectively a forced refresh
                forced_refresh = not self._last_update
                if not self._tag_types:
                    # load_stored_data might itself call _fetch_tag_types if store is empty/invalid
                    # This needs careful chaining of the is_forced_refresh flag or context.
                    # For simplicity, assume load_stored_data doesn't force a fetch that needs to raise.
                    await self.load_stored_data()

                # If still no types or cache expired or forced refresh
                if not self._tag_types or forced_refresh or \
                   (datetime.now() - self._last_update > CACHE_DURATION):
                    await self._fetch_tag_types(is_forced_refresh=forced_refresh or not self._tag_types)
        ```

    *   In `services.py`, `refresh_tag_types_service`:
        Add a `try...except HomeAssistantError` block.
        ```python
        async def refresh_tag_types_service(service: ServiceCall) -> None:
            manager = await get_tag_types_manager(hass)
            manager._last_update = None  # Force refresh flag for the manager
            try:
                await manager.ensure_types_loaded()
                tag_types_len = len(manager.get_all_types())
                message = f"Successfully refreshed {tag_types_len} tag types from GitHub"
                # ... (persistent notification logic)
            except HomeAssistantError: # Re-raise to inform user via UI
                _LOGGER.error("Failed to refresh tag types as expected.")
                raise
            except Exception as e:
                _LOGGER.error("Unexpected error during tag type refresh: %s", str(e))
                raise HomeAssistantError(f"An unexpected error occurred while refreshing tag types: {str(e)}") from e
        ```

6.  **Propagate Failures from `UploadQueueHandler` in `drawcustom_service`**:
    To make `drawcustom_service` fully compliant, failures during the actual `upload_image` step (executed by `UploadQueueHandler`) should be propagated back as an exception from the service call. This is a more involved change:
    *   Modify `UploadQueueHandler.add_to_queue` to return an `asyncio.Future`.
    *   Modify `UploadQueueHandler._process_queue` to set the result or exception on this future.
    *   In `drawcustom_service`, collect these futures for all devices. After the loop, `await asyncio.gather(*futures, return_exceptions=True)` or similar to wait for all uploads.
    *   Iterate through the results, and if any returned an exception, append it to the `errors` list and raise a final `HomeAssistantError`.
    This ensures that `drawcustom_service` only returns "success" if all parts of its operation, including queued uploads, complete successfully. If this architectural change is too complex immediately, at a minimum, ensure robust logging and consider creating persistent notifications for upload failures from the `UploadQueueHandler`. However, for strict rule compliance, the service call itself should raise the exception.

7.  **Consider `ServiceValidationError` for `deprecated_service_handler`**:
    While `HomeAssistantError` is acceptable, `ServiceValidationError` might be more semantically correct for indicating that the user is trying to use a service that is no longer valid ("incorrect usage").
    ```python
    # In services.py, inside deprecated_service_handler
    raise ServiceValidationError( # Changed from HomeAssistantError
        f"The service {DOMAIN}.{old_service} has been removed. "
        f"Please use {DOMAIN}.drawcustom instead. "
        "See the documentation for more details."
    )
    ```

By implementing these suggestions, the `open_epaper_link` integration will better align with the `action-exceptions` rule, leading to improved error reporting and a better user experience.

_Created at 2025-05-14 20:44:30. Prompt tokens: 60482, Output tokens: 3986, Total tokens: 74037_
