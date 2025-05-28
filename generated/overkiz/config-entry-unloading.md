# overkiz: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `config-entry-unloading` rule requires that integrations support config entry unloading, allowing Home Assistant to unload the integration at runtime without a restart. This involves implementing the `async_unload_entry` function to clean up any subscriptions, close connections, and unload platforms.

The `overkiz` integration uses config entries and implements the `async_setup_entry` function to set up its components, including an `OverkizClient` and an `OverkizDataUpdateCoordinator`. The `OverkizClient` is initialized with a dedicated `aiohttp.ClientSession` (created in `create_local_client` or `create_cloud_client` within `homeassistant/components/overkiz/__init__.py`) and performs a login which may register an event listener on the Overkiz server/hub.

The integration currently implements `async_unload_entry` as follows:
```python
# homeassistant/components/overkiz/__init__.py
async def async_unload_entry(
    hass: HomeAssistant, entry: OverkizDataConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```

This implementation correctly unloads the platforms (entities) associated with the config entry. However, it does not perform a full cleanup of all resources created during `async_setup_entry`:

1.  **OverkizClient Logout:** The `OverkizClient` instance (stored in `entry.runtime_data.coordinator.client`) is not explicitly logged out. The `pyoverkiz` library's `client.login()` method (called during setup) typically registers an event listener on the server. This listener should be deregistered via `client.logout()` to free up resources on the hub/server, which can be limited.
2.  **aiohttp.ClientSession Closure:** A new `aiohttp.ClientSession` is created specifically for each `OverkizClient` instance in `create_local_client` and `create_cloud_client`. This session (`client.session`) is not closed when the entry is unloaded, which can lead to resource leaks (e.g., open sockets).

According to the rule, "In the `async_unload_entry` interface function, the integration should clean up any subscriptions and close any connections opened during the setup of the integration." The current implementation only partially fulfills this by unloading platforms.

## Suggestions

To make the `overkiz` integration compliant with the `config-entry-unloading` rule, the `async_unload_entry` function should be updated to include steps for logging out the `OverkizClient` and closing its associated `aiohttp.ClientSession`.

Modify `homeassistant/components/overkiz/__init__.py` as follows:

```python
# homeassistant/components/overkiz/__init__.py
# ... (other imports)
from pyoverkiz.client import OverkizClient # Ensure OverkizClient is imported if not already for type hinting
# ...

async def async_unload_entry(
    hass: HomeAssistant, entry: OverkizDataConfigEntry
) -> bool:
    """Unload a config entry."""
    # First, unload platforms. If this fails, we don't proceed with other cleanup.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Retrieve the client from runtime_data
        # entry.runtime_data is of type HomeAssistantOverkizData
        data: HomeAssistantOverkizData = entry.runtime_data
        client: OverkizClient = data.coordinator.client

        # Log out from the Overkiz client to remove the server-side event listener
        # This is important as hubs/servers might have a limit on active listeners.
        if client.event_listener_id:  # Check if a listener was likely registered
            try:
                LOGGER.debug("Logging out from Overkiz client for entry %s", entry.entry_id)
                await client.logout()
                LOGGER.debug("Successfully logged out from Overkiz client for entry %s", entry.entry_id)
            except Exception as e:
                # Log the error but don't make the unload fail,
                # as platforms are already unloaded.
                LOGGER.warning(
                    "Error during Overkiz client logout on unload for entry %s: %s",
                    entry.entry_id,
                    e,
                )

        # Close the aiohttp client session that was created for this entry
        # The session is stored in client.session by create_local_client/create_cloud_client
        if client.session and not client.session.closed:
            try:
                LOGGER.debug("Closing Overkiz aiohttp session for entry %s", entry.entry_id)
                await client.session.close()
                LOGGER.debug("Overkiz aiohttp session closed for entry %s", entry.entry_id)
            except Exception as e:
                LOGGER.warning(
                    "Error closing Overkiz aiohttp session on unload for entry %s: %s",
                    entry.entry_id,
                    e,
                )
        
        # Home Assistant generally handles clearing entry.runtime_data when the entry is fully unloaded.
        # If HomeAssistantOverkizData contained other manually managed resources, they would be cleaned here too.

    return unload_ok
```

**Reasoning for Changes:**

*   **`client.logout()`**: This call ensures that the event listener registered with the Overkiz hub/server during `client.login()` is properly deregistered. This prevents potential resource exhaustion on the server side, especially if entries are frequently reloaded or reconfigured.
*   **`client.session.close()`**: Since `create_local_client` and `create_cloud_client` functions create a new `aiohttp.ClientSession` for each config entry, it's crucial to close this session when the entry is unloaded. This releases underlying network connections and prevents resource leaks in Home Assistant.
*   **Conditional Cleanup (`if unload_ok`)**: The additional cleanup steps are performed only if `async_unload_platforms` succeeds, which is a common pattern ensuring that primary de-registration happens first.
*   **Error Handling**: Basic error handling is added for the logout and session close operations to prevent the unload process from failing completely if these cleanup steps encounter issues, while still logging the problem.

Alternatively, the cleanup of `client.logout()` and `client.session.close()` could also be managed by registering a callback with `entry.async_on_unload` within the `async_setup_entry` function. This method also ensures cleanup if `async_setup_entry` fails after these resources have been created and the callback registered. However, the provided suggestion directly modifies `async_unload_entry` to align with the style of the example given in the rule's documentation. Both approaches achieve the required cleanup.

_Created at 2025-05-28 12:19:13. Prompt tokens: 87024, Output tokens: 1691, Total tokens: 94855_
