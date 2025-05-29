# nest: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nest](https://www.home-assistant.io/integrations/nest/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires integrations to check during initialization if they can be set up correctly and to raise specific Home Assistant exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) to provide immediate and clear feedback to the user upon failure.

This rule applies to the `nest` integration as it uses config entries and implements an `async_setup_entry` function.

The `nest` integration largely follows this rule by performing several checks and handling exceptions from the `google-nest-sdm` library:

1.  **Authentication Token Retrieval (`auth.async_get_access_token()`):**
    *   It correctly catches `aiohttp.ClientResponseError` and raises `ConfigEntryAuthFailed` for 4xx errors or `ConfigEntryNotReady` for other HTTP errors.
    *   It catches `aiohttp.ClientError` (e.g., network issues) and raises `ConfigEntryNotReady`.
    This is found in `homeassistant/components/nest/__init__.py`:
    ```python
    try:
        await auth.async_get_access_token()
    except ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed from err
        raise ConfigEntryNotReady from err
    except ClientError as err:
        raise ConfigEntryNotReady from err
    ```

2.  **Subscriber Start (`subscriber.start_async()`):**
    *   It correctly catches `google_nest_sdm.exceptions.AuthException` and raises `ConfigEntryAuthFailed`.
    *   It correctly catches `google_nest_sdm.exceptions.SubscriberException` and raises `ConfigEntryNotReady`.
    This is found in `homeassistant/components/nest/__init__.py`:
    ```python
    try:
        unsub = await subscriber.start_async()
    except AuthException as err:
        raise ConfigEntryAuthFailed(
            f"Subscriber authentication error: {err!s}"
        ) from err
    # ... (ConfigurationException handled differently)
    except SubscriberException as err:
        raise ConfigEntryNotReady(f"Subscriber error: {err!s}") from err
    ```

3.  **Device Manager Retrieval (`subscriber.async_get_device_manager()`):**
    *   It correctly catches `google_nest_sdm.exceptions.ApiException` and raises `ConfigEntryNotReady`.
    This is found in `homeassistant/components/nest/__init__.py`:
    ```python
    try:
        device_manager = await subscriber.async_get_device_manager()
    except ApiException as err:
        unsub()
        raise ConfigEntryNotReady(f"Device manager error: {err!s}") from err
    ```

However, the integration does **not fully** follow the rule due to its handling of `google_nest_sdm.exceptions.ConfigurationException` during `subscriber.start_async()`:

*   When a `ConfigurationException` occurs, the integration logs an error and returns `False` instead of raising `ConfigEntryError` or `ConfigEntryNotReady`.
    ```python
    # From homeassistant/components/nest/__init__.py
    except ConfigurationException as err:
        _LOGGER.error("Configuration error: %s", err)
        return False
    ```
    Returning `False` causes the setup to fail more silently from the user's perspective in the UI (it might just show as "Failed to set up" after retries, without a specific error message tied to `ConfigEntryError`). The rule requires raising an appropriate exception to inform the user about the nature of the failure.

## Suggestions

To make the `nest` integration fully compliant with the `test-before-setup` rule, the handling of `ConfigurationException` should be modified:

1.  **Handle `ConfigurationException` by raising `ConfigEntryError`:**
    A `ConfigurationException` from the SDM library typically indicates a persistent issue with the setup (e.g., incorrect Pub/Sub topic configuration, permissions) that is unlikely to be resolved by a simple retry. Raising `ConfigEntryError` provides clear feedback to the user that a configuration problem exists.

    In `homeassistant/components/nest/__init__.py`, change the following block:
    ```python
    # Current code:
    except ConfigurationException as err:
        _LOGGER.error("Configuration error: %s", err)
        return False
    ```
    to:
    ```python
    # Suggested code:
    except ConfigurationException as err:
        _LOGGER.error("Subscriber configuration error: %s", err)
        raise ConfigEntryError(f"Subscriber configuration error: {err!s}") from err
    ```
    **Why this helps:**
    *   This change will result in a clear error message in the Home Assistant UI when such a configuration issue occurs, guiding the user towards resolving it.
    *   It aligns with the rule's intent to "immediately let the user know that it doesn't work" with specific feedback.

_Created at 2025-05-28 22:53:06. Prompt tokens: 32412, Output tokens: 1235, Total tokens: 38517_
