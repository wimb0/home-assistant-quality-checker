# home_connect: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `config-entry-unloading` rule requires that integrations implement the `async_unload_entry` function to clean up all resources, subscriptions, and connections that were established during the `async_setup_entry` phase. This allows Home Assistant to unload the integration at runtime without requiring a full restart.

The `home_connect` integration implements the `async_unload_entry` function. This function correctly calls `hass.config_entries.async_unload_platforms(entry, PLATFORMS)` to unload entities and associated platform resources. It also cleans up specific entries from the issue registry. Additionally, background tasks created using `entry.async_create_background_task` (like the event listener and initial refresh task) are automatically cancelled by Home Assistant when a config entry is unloaded. Callbacks registered via `entry.async_on_unload` (used in `sensor.py` and `common.py` for listener cleanup) are also correctly invoked.

However, the integration does not explicitly close the network connection resources held by the `aiohomeconnect.Client`. In `async_setup_entry`, an instance of `HomeConnectClient` is created:
```python
# homeassistant/components/home_connect/__init__.py
# ...
    home_connect_client = HomeConnectClient(config_entry_auth)
    coordinator = HomeConnectCoordinator(hass, entry, home_connect_client)
    entry.runtime_data = coordinator
# ...
```
This `home_connect_client` (accessible via `entry.runtime_data.client`) internally creates an `aiohttp.ClientSession` if one is not provided. This session manages network connections to the Home Connect API, including the event stream. According to the rule, such connections must be closed during unload.

The current `async_unload_entry` function in `homeassistant/components/home_connect/__init__.py` is:
```python
async def async_unload_entry(
    hass: HomeAssistant, entry: HomeConnectConfigEntry
) -> bool:
    """Unload a config entry."""
    issue_registry = ir.async_get(hass)
    issues_to_delete = [
        "deprecated_set_program_and_option_actions",
        "deprecated_command_actions",
    ] + [
        issue_id
        for (issue_domain, issue_id) in issue_registry.issues
        if issue_domain == DOMAIN
        and issue_id.startswith("home_connect_too_many_connected_paired_events")
    ]
    for issue_id in issues_to_delete:
        issue_registry.async_delete(DOMAIN, issue_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```
This implementation is missing the step to close the `aiohomeconnect.Client`'s resources.

## Suggestions

To comply with the `config-entry-unloading` rule, the `async_unload_entry` function should be updated to close the `aiohomeconnect.Client` instance, which is stored within the coordinator in `entry.runtime_data`. This will ensure that its underlying `aiohttp.ClientSession` and any active network connections (including the event stream) are properly terminated.

Modify `homeassistant/components/home_connect/__init__.py` as follows:

```python
async def async_unload_entry(
    hass: HomeAssistant, entry: HomeConnectConfigEntry
) -> bool:
    """Unload a config entry."""
    issue_registry = ir.async_get(hass)
    issues_to_delete = [
        "deprecated_set_program_and_option_actions",
        "deprecated_command_actions",
    ] + [
        issue_id
        for (issue_domain, issue_id) in issue_registry.issues
        if issue_domain == DOMAIN
        and issue_id.startswith("home_connect_too_many_connected_paired_events")
    ]
    for issue_id in issues_to_delete:
        issue_registry.async_delete(DOMAIN, issue_id)

    # Unload platforms and associated entities/listeners
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up the coordinator and its resources
        coordinator: HomeConnectCoordinator = entry.runtime_data
        if coordinator and coordinator.client:
            # The aiohomeconnect.Client has an async close() method
            # which will close its internally managed aiohttp.ClientSession.
            await coordinator.client.close()
        # Optionally, clear runtime_data, though the entry itself is being unloaded.
        # entry.runtime_data = None

    return unload_ok
```

**Why this change satisfies the rule:**
*   **Closes Connections:** The added `await coordinator.client.close()` call explicitly closes the `aiohttp.ClientSession` managed by the `aiohomeconnect` library. This releases network sockets and stops any ongoing communication like the event stream, preventing resource leaks and ensuring a clean unload.
*   **Follows Pattern:** This change adheres to the common pattern of cleaning up custom resources after successfully unloading platforms, as shown in the rule's example and best practices.

_Created at 2025-05-14 15:35:32. Prompt tokens: 136660, Output tokens: 1311, Total tokens: 143742_
