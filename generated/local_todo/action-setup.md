# local_todo: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not register any custom service actions. It provides a `todo` platform entity, and standard `todo` services are handled by the `todo` component, not registered directly by `local_todo`. |

## Overview

The rule `action-setup` mandates that if an integration adds its own custom service actions, these actions should be registered within the `async_setup` function of the integration (typically in `__init__.py`). This ensures that service definitions are available and can be validated even if no configuration entry for the integration is loaded.

This rule does **not apply** to the `local_todo` integration. Here's why:

1.  **No Custom Service Registration:** The `local_todo` integration primarily provides a `TodoListEntity` for the `todo` domain, as seen in `homeassistant/components/local_todo/todo.py`. The services associated with this entity (e.g., `todo.add_item`, `todo.update_item`, `todo.remove_item`) are standard services for the `todo` domain. These services are typically registered by the `todo` component itself (the overarching component managing all `todo` entities in Home Assistant) by inspecting the features supported by the `LocalTodoListEntity`. The `local_todo` integration does not call `hass.services.async_register` to define and register its own unique, custom services.

2.  **Code Structure:**
    *   There is no `async_setup` function defined in `homeassistant/components/local_todo/__init__.py`. If the integration were to register custom services according to this rule, they would be expected in such a function.
    *   A review of the entire `local_todo` codebase does not reveal any direct calls to `hass.services.async_register(DOMAIN, ...)` which would indicate the registration of a custom service specific to `local_todo`.

The `action-setup` rule is designed for integrations that introduce new services beyond what standard entity platforms offer. For example, if `local_todo` had a service like `local_todo.export_all_lists_to_cloud`, that would be a custom service, and its registration would fall under this rule. Since `local_todo` only implements the standard `todo` platform, and relies on the `todo` component to expose its functionalities as services, the `action-setup` rule is not applicable.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:25:56. Prompt tokens: 5186, Output tokens: 629, Total tokens: 8395_
