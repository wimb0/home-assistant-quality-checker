# open_epaper_link: stale-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [stale-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/stale-devices)                                                     |
| Status | **todo**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `stale-devices` rule applies to the `open_epaper_link` integration as it manages devices (ePaper tags) connected to a central hub (the OpenEPaperLink AP). These tags can be removed from the AP or become unavailable, and Home Assistant should reflect these changes by removing the stale device entries.

The integration attempts to follow this rule by implementing an automatic device removal mechanism. Specifically, in `homeassistant/components/open_epaper_link/hub.py`:
- The `Hub` class maintains a list of known tags (`self._known_tags`).
- The `_verify_and_cleanup_tags` method is responsible for identifying stale devices. It calls `_fetch_all_tags_from_ap` to get the current list of tags directly from the AP.
- It then compares the AP's list with `self._known_tags`. Any tag present in `self._known_tags` but not in the list from the AP is considered stale.
- For each stale tag, `_remove_tag` is called, which uses `device_registry.async_remove_device(device_id)` to remove the device and its associated entities from Home Assistant. This check is triggered on WebSocket (re)connection and when the AP reports a decrease in its `recordcount`.

However, the integration currently does **NOT** fully follow the rule due to a critical issue in its stale device detection:
1.  **Erroneous Removal on AP Unavailability:** The `_fetch_all_tags_from_ap` method, if it encounters an error communicating with the AP (e.g., AP is offline, network issue), will return an empty or incomplete list of tags. The calling method, `_verify_and_cleanup_tags`, does not currently check for such a fetch failure. It proceeds to compare `self._known_tags` against this empty/incomplete list, leading it to incorrectly identify all (or many) existing devices as stale. Consequently, it will attempt to remove devices that are not actually gone but merely unconfirmable due to temporary AP unavailability. This violates the principle "We should only remove devices that we are sure are no longer available."

2.  **Missing Manual Removal Fallback:** The integration does not implement the `async_remove_config_entry_device` function in `__init__.py`. This function allows users to manually delete a device from the device registry UI if the automatic cleanup fails or if a device becomes orphaned for other reasons. While a robust automatic system is preferred, providing this fallback is good practice, especially if the automatic system cannot be 100% certain in all edge cases (like permanent AP failure).

## Suggestions

To make the `open_epaper_link` integration compliant with the `stale-devices` rule, the following changes are recommended:

1.  **Prevent Erroneous Device Removal on AP Fetch Failure:**
    Modify `_fetch_all_tags_from_ap` in `homeassistant/components/open_epaper_link/hub.py` to clearly signal failure (e.g., by returning `None` or raising an exception). Then, update `_verify_and_cleanup_tags` to check for this failure signal and skip the device removal logic if the current list of tags could not be reliably fetched from the AP.

    **Example (conceptual change in `hub.py`):**
    ```python
    # In class Hub:
    async def _fetch_all_tags_from_ap(self) -> dict | None: # Modified to return None on failure
        result = {}
        position = 0
        try:
            # ... existing logic ...
            # Inside the loop, if a request fails or returns non-200:
            # if response.status_code != 200:
            #     _LOGGER.error("Failed to fetch all tags from AP: %s", response.text)
            #     return None # Indicate failure
            # ...
        except Exception as err: # Catch exceptions from requests or JSON parsing
            _LOGGER.error("Failed to fetch all tags from AP: %s", str(err))
            return None # Indicate failure
        return result

    async def _verify_and_cleanup_tags(self) -> None:
        try:
            ap_tags_data = await self._fetch_all_tags_from_ap()

            if ap_tags_data is None:
                _LOGGER.warning("Could not fetch tag list from AP. Skipping stale device check to prevent erroneous removals.")
                return

            ap_macs = set(ap_tags_data.keys())
            # ... rest of existing comparison and removal logic ...
            # deleted_tags = known_macs_upper - ap_macs_upper
            # ...
        except Exception as err:
            _LOGGER.error(f"Error while verifying AP tags: {err}")
    ```
    *Why this helps:* This change ensures that devices are only removed if the AP positively confirms they are gone by providing a complete list of active tags. If the AP is unreachable, the integration will not assume all devices are stale.

2.  **Implement `async_remove_config_entry_device`:**
    Add the `async_remove_config_entry_device` function to `homeassistant/components/open_epaper_link/__init__.py`. This will enable a "Delete" button in the device UI, allowing users to manually remove devices if needed. The function should return `True` if the device is confirmed to be no longer available (e.g., not in the hub's current list of active tags).

    **Example (in `__init__.py`):**
    ```python
    # Add to homeassistant/components/open_epaper_link/__init__.py
    from homeassistant.helpers import device_registry as dr
    from .hub import Hub # Ensure Hub can be imported or accessed via hass.data

    # ... (other imports and code) ...

    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
    ) -> bool:
        """Allow manual removal of a device if it's no longer active."""
        hub: Hub = hass.data[DOMAIN][config_entry.entry_id]

        device_mac = None
        for identifier in device_entry.identifiers:
            if identifier[0] == DOMAIN:
                device_mac = identifier[1]
                break

        if not device_mac:
            # Should not happen for devices created by this integration
            return False

        # Check against the hub's current list of known (non-blacklisted) tags.
        # hub.tags is a list of MAC addresses.
        is_known_and_active = any(known_mac.upper() == device_mac.upper() for known_mac in hub.tags)

        # Allow removal if the device is not in the hub's current list of active tags.
        # If hub is offline, hub.tags might be stale, but this function is a user-initiated
        # action, often used when the system state is perceived as incorrect by the user.
        # Returning `not is_known_and_active` means if HA *thinks* it's gone, user can delete.
        return not is_known_and_active
    ```
    *Why this helps:* This provides a user-controlled mechanism to clean up devices that might have been missed by automatic cleanup or persisted due to prolonged AP issues. It aligns with the rule's recommendation for situations where absolute certainty about a device's status is difficult to maintain automatically at all times.

_Created at 2025-05-14 21:09:31. Prompt tokens: 60898, Output tokens: 1825, Total tokens: 69660_
