# local_calendar: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_calendar](https://www.home-assistant.io/integrations/local_calendar/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **exempt**                                       |
| Reason | This integration does not register any custom services under its own domain; it provides a calendar platform whose services are registered by the `calendar` component. |

## Overview

The `action-setup` rule mandates that integrations registering their own custom service actions should do so within the `async_setup` function, rather than `async_setup_entry`. This ensures that service definitions are always available for tasks like automation validation, even if a specific configuration entry for the integration is not currently loaded.

This rule does not apply to the `local_calendar` integration. Here's why:

1.  **No Custom Domain-Specific Services:** The `local_calendar` integration does not define or register any custom services under its own domain (e.g., `local_calendar.my_custom_action`). An inspection of its `__init__.py` file, which is the typical place for such registrations, shows no calls to `hass.services.async_register` for services specific to the `local_calendar` domain.

2.  **Platform Implementation:** `local_calendar` functions as a platform for the `calendar` component. This is declared in `local_calendar/__init__.py`:
    ```python
    PLATFORMS: list[Platform] = [Platform.CALENDAR]
    ```
    The `local_calendar/calendar.py` file defines `LocalCalendarEntity`, which implements standard calendar entity methods such as `async_create_event`, `async_delete_event`, and `async_update_event`. These methods serve as handlers for generic calendar services (e.g., `calendar.create_event`, `calendar.delete_event`) that are registered by the `calendar` component itself, not by `local_calendar`.

3.  **Rule Scope:** The `action-setup` rule, including its example implementation, focuses on integrations that add *their own* service actions:
    ```python
    # Example from rule documentation
    hass.services.async_register(
        DOMAIN,  # The integration's domain
        SERVICE_GET_SCHEDULE, # A custom service name
        async_get_schedule,
        # ...
    )
    ```
    Since `local_calendar` does not follow this pattern of registering services under its own domain, the requirements for *where* these registrations should occur (i.e., in `async_setup`) are not applicable. The services it interacts with (like `calendar.create_event`) are managed and registered by the central `calendar` integration, which would be subject to this rule for its own service registrations.

In summary, `local_calendar` provides an implementation for a standard platform, and does not introduce its own new services that would fall under the scope of the `action-setup` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:20:33. Prompt tokens: 6561, Output tokens: 706, Total tokens: 10661_
