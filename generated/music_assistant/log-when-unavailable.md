# music_assistant: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable)                                                     |
| Status | **todo**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `log-when-unavailable` rule requires that an integration logs a message at `INFO` level when the device or service it depends on becomes unavailable, and again when it becomes available. This logging should only occur once per state change to avoid spamming logs.

This rule applies to the `music_assistant` integration as it connects to an external Music Assistant server, which can become unavailable due to network issues, server downtime, or configuration problems. The integration's entities (media players) depend on this connection.

The integration currently does not fully adhere to this rule:

1.  **Initial Connection Failure (`__init__.py` - `async_setup_entry`):**
    *   When `mass.connect()` fails due to `TimeoutError` or `CannotConnect`, `ConfigEntryNotReady` is raised. Home Assistant core logs this as a WARNING, but the integration itself does not emit a specific `LOGGER.info` message detailing the unavailability of the Music Assistant server.
    *   For `InvalidServerVersion`, an issue is created, and `ConfigEntryNotReady` is raised, again without a specific `LOGGER.info` from the integration about the service being effectively unavailable.
    *   For other `MusicAssistantError` during initial connection, `LOGGER.exception` is used (ERROR level), followed by `ConfigEntryNotReady`.

2.  **Runtime Disconnection (`__init__.py` - `_client_listen`):**
    *   If the `mass.start_listening()` task terminates due to `MusicAssistantError` or another `Exception` after the integration is loaded, messages are logged at `ERROR` or `EXCEPTION` level (e.g., `LOGGER.error("Failed to listen: %s", err)`).
    *   A `LOGGER.debug("Disconnected from server. Reloading integration")` message is logged before a reload is scheduled.
    *   None of these are the required `INFO` level message specifically stating that the "Music Assistant server became unavailable."

3.  **Reconnection / Becoming Available:**
    *   After a disconnection and reload, if `async_setup_entry` successfully connects and sets up, there is no specific `LOGGER.info` message like "Music Assistant server is back online" or "Connection to Music Assistant server re-established." While various setup steps might log their own messages, a clear "back online" log at `INFO` level for the service connection is missing.

The `DataUpdateCoordinator` pattern, which has built-in support for this logging behavior, is not used for managing the main connection to the Music Assistant server. Therefore, the integration needs to implement this logging manually.

## Suggestions

To comply with the `log-when-unavailable` rule, the following changes are recommended:

1.  **Log on Initial Connection Failure in `async_setup_entry`:**
    Before raising `ConfigEntryNotReady` for connection-related issues, log an `INFO` message.

    *File: `homeassistant/components/music_assistant/__init__.py`*
    ```python
    # ...
    try:
        async with asyncio.timeout(CONNECT_TIMEOUT):
            await mass.connect()
    except (TimeoutError, CannotConnect) as err:
        # ADD THIS INFO LOG
        LOGGER.info(
            "Connection to Music Assistant server %s failed: %s. Setup will be retried.",
            mass_url,
            err,
        )
        raise ConfigEntryNotReady(
            f"Failed to connect to music assistant server {mass_url}"
        ) from err
    except InvalidServerVersion as err:
        async_create_issue(
            hass,
            DOMAIN,
            "invalid_server_version",
            is_fixable=False,
            severity=IssueSeverity.ERROR,
            translation_key="invalid_server_version",
        )
        # ADD THIS INFO LOG
        LOGGER.info(
            "Connection to Music Assistant server %s failed due to incompatible server version: %s. Setup will be retried.",
            mass_url,
            err
        )
        raise ConfigEntryNotReady(f"Invalid server version: {err}") from err
    except MusicAssistantError as err:
        # ADD THIS INFO LOG (or ensure existing LOGGER.exception is complemented by a clear INFO message if needed)
        LOGGER.info(
            "Connection to Music Assistant server %s failed with an error: %s. Setup will be retried.",
            mass_url,
            err
        )
        LOGGER.exception("Failed to connect to music assistant server", exc_info=err)
        raise ConfigEntryNotReady(
            f"Unknown error connecting to the Music Assistant server {mass_url}"
        ) from err
    # ...
    ```

2.  **Log on Runtime Disconnection in `_client_listen`:**
    When the `mass.start_listening()` task fails or exits unexpectedly after the integration was successfully loaded, log an `INFO` message.

    *File: `homeassistant/components/music_assistant/__init__.py`*
    ```python
    async def _client_listen(
        hass: HomeAssistant,
        entry: MusicAssistantConfigEntry, # Corrected type hint
        mass: MusicAssistantClient,
        init_ready: asyncio.Event,
    ) -> None:
        """Listen with the client."""
        try:
            await mass.start_listening(init_ready)
        except MusicAssistantError as err:
            if entry.state == ConfigEntryState.LOADED:
                # ADD THIS INFO LOG
                LOGGER.info("Connection to Music Assistant server lost: %s. Will attempt to reload.", err)
            # Existing error logging can remain for more detailed diagnostics
            if entry.state != ConfigEntryState.LOADED:
                raise
            LOGGER.error("Failed to listen: %s", err)
        except Exception as err:  # pylint: disable=broad-except
            if entry.state == ConfigEntryState.LOADED:
                # ADD THIS INFO LOG
                LOGGER.info(
                    "Connection to Music Assistant server lost due to an unexpected error: %s. Will attempt to reload.", err
                )
            # Existing exception logging can remain
            if entry.state != ConfigEntryState.LOADED:
                raise
            LOGGER.exception("Unexpected exception: %s", err)

        if not hass.is_stopping:
            # The INFO log above now serves as the primary "unavailable" notification.
            # The DEBUG log below can be kept for more detailed flow information or removed if redundant.
            LOGGER.debug("Disconnected from server. Reloading integration")
            hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
    ```

3.  **Log When Connection is Re-established (or Initially Established) in `async_setup_entry`:**
    After a successful connection and client readiness, log an `INFO` message. This message will serve as the "back online" log if a previous disconnection was logged, or as an initial "connected" log.

    *File: `homeassistant/components/music_assistant/__init__.py`*
    ```python
    # In async_setup_entry, after successful init_ready.wait()

    # store the listen task and mass client in the entry data
    entry.runtime_data = MusicAssistantEntryData(mass, listen_task)

    # ADD THIS INFO LOG - Indicates successful connection and client readiness
    LOGGER.info("Successfully connected to Music Assistant server %s and client is ready.", mass_url)

    # If the listen task is already failed, we need to raise ConfigEntryNotReady
    # ... (rest of the function)
    ```
    To strictly implement "log once when back connected" (i.e., only if it was previously logged as unavailable), a state-tracking mechanism would be needed that persists across integration reloads (e.g., using a flag stored outside `entry.runtime_data`, perhaps in `hass.data` keyed by `entry.entry_id`, or if the `MusicAssistantClient` itself managed and exposed this state). The suggestion above provides a general "connected and ready" log, which in the context of a preceding "unavailable" log, fulfills the rule's intent.

These changes will ensure that users have clear `INFO` level logs indicating when the Music Assistant server becomes unavailable and when the connection is restored, aiding in troubleshooting and understanding the integration's status.

_Created at 2025-05-13 10:12:02. Prompt tokens: 30406, Output tokens: 1999, Total tokens: 41370_
