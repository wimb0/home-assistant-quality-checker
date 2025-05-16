# linkplay: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule applies to the `linkplay` integration because it involves setting up communication with a network-connected device, and it's crucial to verify this communication during the initialization of the config entry.

The `linkplay` integration **follows** this rule.

In its `__init__.py`, the `async_setup_entry` function performs the necessary checks:
```python
async def async_setup_entry(hass: HomeAssistant, entry: LinkPlayConfigEntry) -> bool:
    """Async setup hass config entry. Called when an entry has been setup."""

    session: ClientSession = await async_get_client_session(hass)
    bridge: LinkPlayBridge | None = None

    # try create a bridge
    try:
        bridge = await linkplay_factory_httpapi_bridge(entry.data[CONF_HOST], session)
    except LinkPlayRequestException as exception:
        raise ConfigEntryNotReady(
            f"Failed to connect to LinkPlay device at {entry.data[CONF_HOST]}"
        ) from exception

    # ... rest of the setup ...
    
    entry.runtime_data = LinkPlayData(bridge=bridge)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
```

Specifically:
1.  It attempts to establish a connection and create a `LinkPlayBridge` instance by calling `await linkplay_factory_httpapi_bridge(entry.data[CONF_HOST], session)`. This call serves as the test to ensure the device is reachable and can be communicated with.
2.  This crucial operation is wrapped in a `try...except` block. If `linkplay_factory_httpapi_bridge` fails (e.g., the device is offline, the host is incorrect, or there's another network issue), it is expected to raise a `LinkPlayRequestException`.
3.  Upon catching `LinkPlayRequestException`, the integration correctly raises `ConfigEntryNotReady`. This informs Home Assistant that the setup could not be completed due to a potentially temporary issue, and Home Assistant will automatically retry the setup later. This aligns with the rule's guidance for handling transient failures like an offline device.

The `linkplay` integration primarily relies on the host IP address for connection and does not involve user credentials or API keys during `async_setup_entry`. Therefore, raising `ConfigEntryAuthFailed` is not applicable in this context.

While `LinkPlayRequestException` is a somewhat generic exception from the underlying library, raising `ConfigEntryNotReady` is a suitable and common handling strategy for network device integrations where the exact cause of a connection failure might not always be distinguishable as definitively temporary or permanent without further context. The current implementation ensures that setup does not proceed if the initial connection test fails, providing a good user experience by not setting up a non-functional integration.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:13:27. Prompt tokens: 10935, Output tokens: 758, Total tokens: 14630_
