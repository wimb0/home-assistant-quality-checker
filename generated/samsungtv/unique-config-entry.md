```markdown
# samsungtv: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                       |
| Reason | |

## Overview

This rule requires that an integration prevents users from setting up the same device or service multiple times. This is typically enforced by setting a `unique_id` on the `ConfigEntry` and/or by checking for existing entries based on unique data points like host or device identifiers.

The `samsungtv` integration fully follows this rule. It implements uniqueness checks in its `config_flow.py` using the recommended methods.

1.  **Using `unique_id`:** The integration attempts to retrieve a unique identifier (UDN or device ID) from the Samsung TV itself via the `async_get_device_info` method in `bridge.py`.
    *   In `config_flow.py`, the `_async_set_device_unique_id` method (called by `async_step_user`, `async_step_ssdp`, `async_step_dhcp`, and `async_step_zeroconf`) fetches this device info.
    *   It then calls `self.async_set_unique_id(self._udn)` where `self._udn` is the extracted unique device name/identifier (`_strip_uuid(dev_info.get("udn", info["id"]))`).
    *   Immediately after setting the unique ID, it calls `self._abort_if_unique_id_configured()`. This built-in `ConfigFlow` method checks if another entry with the same unique ID already exists and aborts the current flow, preventing duplicates.
2.  **Handling Different Discovery Methods:** The integration supports manual configuration (`async_step_user`), SSDP (`async_step_ssdp`), DHCP (`async_step_dhcp`), and Zeroconf (`async_step_zeroconf`) discovery. All these methods converge on the logic to set the unique ID and check for existing entries based on that ID, ensuring consistency regardless of how the device was discovered.
3.  **Updating Existing Entries:** The `_async_update_existing_matching_entry` method in `config_flow.py` further enhances uniqueness handling. If a device is discovered via a method that provides a more robust identifier (like a UDN or MAC) than a potentially incomplete existing entry (e.g., set up only by host), this method updates the existing entry with the new information and reloads it, preventing a new entry from being created with the better identifier.
4.  **Initial Host Check:** As a preliminary check in `async_step_user`, before potentially retrieving device info, the flow also uses `self._async_abort_entries_match({CONF_HOST: self._host})`. While the UDN is the primary unique key, preventing setup of the same host is also a reasonable initial check.

By employing `self.async_set_unique_id` based on the device identifier (UDN/ID) and using `self._abort_if_unique_id_configured`, combined with logic to update entries from different discovery sources and a basic host check, the integration effectively prevents duplicate config entries for the same physical device.

## Suggestions

No suggestions needed. The integration correctly implements the requirements of this rule.
```

_Created at 2025-05-25 11:29:15. Prompt tokens: 30760, Output tokens: 792, Total tokens: 32711_
