```markdown
# pegel_online: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **done**                                                                 |

## Overview

The `test-before-setup` rule requires integrations to perform a check during their initialization (`async_setup_entry`) to verify that they can connect to the device or service successfully. If this initial check fails, the integration should raise a specific exception (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, or `ConfigEntryError`) to inform the user and Home Assistant about the setup failure.

This rule applies to the `pegel_online` integration as it connects to an external service.

The `pegel_online` integration follows this rule. In its `async_setup_entry` function located in `homeassistant/components/pegel_online/__init__.py`, it performs an initial API call (`await api.async_get_station_details(station_uuid)`) within a `try...except CONNECT_ERRORS` block. If a connection error occurs during this initial call, it raises `ConfigEntryNotReady`.

Furthermore, the integration uses a `DataUpdateCoordinator` and calls `await coordinator.async_config_entry_first_refresh()` immediately after creating the coordinator. As noted in the rule's description, utilizing `async_config_entry_first_refresh()` implicitly satisfies the rule. The `_async_update_data` method in the `PegelOnlineDataUpdateCoordinator` (`homeassistant/components/pegel_online/coordinator.py`) also handles `CONNECT_ERRORS` by raising `UpdateFailed`. When `async_config_entry_first_refresh()` encounters an `UpdateFailed` exception, Home Assistant correctly interprets this as a temporary failure and raises `ConfigEntryNotReady`, adhering to the requirement of the rule.

The combination of the initial check for station details and the use of `async_config_entry_first_refresh()` with appropriate error handling in the coordinator ensures that the integration tests connectivity before completing the setup process.

## Suggestions

No suggestions needed. The integration follows the rule.
```

_Created at 2025-05-25 11:22:47. Prompt tokens: 5948, Output tokens: 532, Total tokens: 7404_
