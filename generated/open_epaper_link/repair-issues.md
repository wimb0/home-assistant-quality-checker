# open_epaper_link: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `repair-issues` rule requires integrations to use Home Assistant's repair issue system to notify users about problems that require their intervention and are fixable by them. This provides a user-friendly way to communicate issues and guide users towards a resolution.

This rule applies to the `open_epaper_link` integration because it communicates with a local hardware device (the OpenEPaperLink Access Point or AP). This AP can become unavailable due to network issues, power problems, or other misconfigurations that the user can typically resolve.

The `open_epaper_link` integration currently does **not** follow this rule. It does not use the `homeassistant.helpers.issue_registry` to create repair issues when user-intervention is needed for such problems.

Specifically, there are two main scenarios where repair issues would be beneficial:

1.  **AP Unavailability After Successful Setup:**
    In `homeassistant/components/open_epaper_link/hub.py`, the `_websocket_handler` method manages the WebSocket connection to the AP. If this connection fails (e.g., due to `aiohttp.ClientError` or other exceptions), the `online` status of the hub is set to `False`, an error is logged, and a `_connection_status` signal is dispatched.
    ```python
    # hub.py - _websocket_handler method
    except aiohttp.ClientError as err:
        self.online = False
        _LOGGER.error("WebSocket connection error: %s", err)
        async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", False)
    except Exception as err:
        self.online = False
        _LOGGER.error("Unexpected WebSocket error: %s", err)
        async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", False)

    if not self._shutdown.is_set():
        await asyncio.sleep(RECONNECT_INTERVAL) # Attempts to reconnect
    ```
    While the integration attempts to reconnect, it does not create a persistent repair issue to inform the user that the AP is offline and what they might do to fix it (e.g., "OpenEPaperLink AP at {host} is unreachable. Please check its power and network connection.").

2.  **Initial Setup Failure:**
    In `homeassistant/components/open_epaper_link/hub.py`, the `async_setup_initial` method performs initial setup tasks, including fetching information from the AP. If critical parts of this process fail due to an exception (e.g., AP is offline, host misconfigured), the method's main `try...except` block catches the error, logs it, and returns `False`.
    ```python
    # hub.py - async_setup_initial method
    except Exception as err: # Catches failures from e.g. async_update_ap_info()
        _LOGGER.error("Failed to set up hub: %s", err)
        return False
    ```
    This `False` return value causes `async_setup_entry` in `homeassistant/components/open_epaper_link/__init__.py` to also return `False`, leading Home Assistant to retry the setup. During these retries, the user is not actively informed via a repair issue that there's a problem they might need to address for the setup to succeed.

In both scenarios, the integration relies on logs or entities becoming unavailable, rather than leveraging the repair issue system for direct, actionable user notification. No import or usage of `homeassistant.helpers.issue_registry` (commonly aliased as `ir`) is found in the codebase.

## Suggestions

To make the `open_epaper_link` integration compliant with the `repair-issues` rule, implement repair issues for user-fixable problems. Below are suggestions for the two scenarios identified:

**1. Handling AP Unavailability After Successful Setup (WebSocket Connection Failure)**

*   **Import `issue_registry`**:
    In `homeassistant/components/open_epaper_link/hub.py`, add the import:
    ```python
    from homeassistant.helpers import issue_registry as ir
    ```

*   **Define Issue ID and Translation Key**:
    Create a unique issue ID for AP unavailability, e.g., `ISSUE_AP_UNAVAILABLE = "ap_unavailable"`.
    Add a corresponding entry to `strings.json` for `issues.ap_unavailable.title` and `issues.ap_unavailable.description`. The description should guide the user (e.g., "The OpenEPaperLink Access Point at {host} is currently unreachable. Please check its power supply and network connection.").

*   **Create Repair Issue on Connection Loss**:
    In `hub.py`, within the `_websocket_handler` method, when a connection error occurs and `self.online` is set to `False`:
    ```python
    # ... inside except aiohttp.ClientError or except Exception blocks ...
    if self.online is False: # Check if status actually changed to offline
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            ISSUE_AP_UNAVAILABLE,
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=ir.IssueSeverity.ERROR,
            translation_key="ap_unavailable", # Matches strings.json
            translation_placeholders={"host": self.host},
        )
    # ...
    ```
    Ensure this is called only once when the state transitions to offline.

*   **Clear Repair Issue on Reconnection**:
    Still in `_websocket_handler`, when the WebSocket connection is successfully (re-)established and `self.online` is set to `True`:
    ```python
    # ... after ws_connect succeeds and self.online = True ...
    if self.online is True: # Check if status actually changed to online
        ir.async_delete_issue(self.hass, DOMAIN, ISSUE_AP_UNAVAILABLE)
    # ...
    ```
    Ensure this is called only once when the state transitions to online.

**2. Handling Initial Setup Failure (Connection Issues during `async_setup_initial`)**

*   **Import `issue_registry`** (if not already done for suggestion 1) in `homeassistant/components/open_epaper_link/hub.py`.

*   **Define Issue ID and Translation Key**:
    Create a unique issue ID, e.g., `ISSUE_INITIAL_SETUP_FAILED = "initial_setup_failed"`.
    Add corresponding entries to `strings.json` for `issues.initial_setup_failed.title` and `issues.initial_setup_failed.description` (e.g., "Failed to connect to the OpenEPaperLink Access Point at {host} during initial setup. Error: {error}. Please verify the AP's status and configuration.").

*   **Create Repair Issue on Setup Failure**:
    In `hub.py`, within the `async_setup_initial` method's main `except Exception as err:` block, before returning `False`:
    ```python
    except Exception as err:
        _LOGGER.error("Failed to set up hub: %s", err)
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            ISSUE_INITIAL_SETUP_FAILED,
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=ir.IssueSeverity.ERROR,
            translation_key="initial_setup_failed", # Matches strings.json
            translation_placeholders={"host": self.host, "error": str(err)},
        )
        # Consider raising ConfigEntryNotReady here if you want HA to explicitly show "Retrying setup"
        # For now, returning False will also cause retries.
        return False
    ```

*   **Clear Repair Issue on Successful Setup**:
    At the beginning of the `try` block in `async_setup_initial` in `hub.py`, clear any pre-existing setup failure issue:
    ```python
    async def async_setup_initial(self) -> bool:
        try:
            # Clear any previous setup failure issue at the start of a new attempt
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_INITIAL_SETUP_FAILED)

            # Load stored data
            stored = await self._store.async_load()
            # ... rest of the method
    ```

By implementing these suggestions, the `open_epaper_link` integration will provide better feedback to users when actionable problems occur, aligning with the `repair-issues` quality scale rule. Remember to add the necessary translation keys to `strings.json` to provide user-friendly messages.

_Created at 2025-05-14 21:07:59. Prompt tokens: 60448, Output tokens: 2053, Total tokens: 67681_
