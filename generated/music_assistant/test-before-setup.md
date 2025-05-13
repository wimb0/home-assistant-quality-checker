# music_assistant: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires that integrations check during their initialization phase if they can be set up correctly and raise appropriate Home Assistant exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) to inform the user of any issues.

This rule applies to the `music_assistant` integration as it connects to an external Music Assistant server, and this connection needs to be verified during setup.

The `music_assistant` integration **fully follows** this rule. The `async_setup_entry` function in `homeassistant/components/music_assistant/__init__.py` implements several checks:

1.  **Initial Connection Attempt (`mass.connect()`):**
    *   It attempts to connect to the Music Assistant server specified by the URL in the config entry.
    *   A `CONNECT_TIMEOUT` is used for this operation.
    *   **Error Handling:**
        *   If a `TimeoutError` or `music_assistant_client.exceptions.CannotConnect` occurs, it raises `ConfigEntryNotReady`, indicating a temporary failure and prompting Home Assistant to retry later. (Lines 60-63)
        *   If an `music_assistant_client.exceptions.InvalidServerVersion` occurs, it creates a persistent issue in Home Assistant, logs an error, and raises `ConfigEntryNotReady`. This informs the user about the version mismatch and allows retries, which is useful if the user is in the process of updating their Music Assistant server. (Lines 64-70)
        *   For other `music_assistant_models.errors.MusicAssistantError` exceptions during connection, it logs the error and raises `ConfigEntryNotReady`. (Lines 71-75)

2.  **Client Listener Initialization (`init_ready.wait()`):**
    *   After the initial connection, it starts a background task (`_client_listen`) to establish a persistent listener with the Music Assistant server.
    *   It waits for an `init_ready` event, which is set by the `_client_listen` task upon successful listener startup, with a `LISTEN_READY_TIMEOUT`.
    *   **Error Handling:**
        *   If this `init_ready.wait()` times out, it cancels the listener task and raises `ConfigEntryNotReady`, indicating the client failed to become fully operational. (Lines 82-87)

3.  **Listener Task Health Check:**
    *   After the `init_ready` event (or timeout), it checks if the `listen_task` has already completed with an exception.
    *   **Error Handling:**
        *   If the `listen_task` (running `_client_listen`) failed during this initial setup phase (e.g., `_client_listen` raised an error because `entry.state` was not yet `ConfigEntryState.LOADED`), the exception is retrieved, platforms are unloaded, the client is disconnected, and `ConfigEntryNotReady` is raised with the underlying error. This ensures that failures in the listener's startup sequence also prevent the integration from loading. (Lines 91-97, and `_client_listen` lines 141-148)

The integration does not use `ConfigEntryAuthFailed` because its configuration flow only involves a URL, not user credentials managed by Home Assistant. If the Music Assistant server itself has authentication and denies connection, this would likely manifest as a `CannotConnect` or a generic `MusicAssistantError`, for which `ConfigEntryNotReady` is appropriate as Home Assistant cannot manage or prompt for re-authentication in this scenario.

The use of `ConfigEntryNotReady` for all identified setup failures is appropriate, as these issues (connectivity, server version, client readiness) are often resolvable by user action or are transient, making retries beneficial.

## Suggestions

No suggestions needed.

_Created at 2025-05-13 10:05:39. Prompt tokens: 30167, Output tokens: 954, Total tokens: 35286_
