# local_todo: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not use a data update coordinator pattern and only defines a single entity type, making the `coordinator.py` and `entity.py` common modules inapplicable. |

## Overview

The `common-modules` rule specifies that common Home Assistant patterns, such as data update coordinators and base entity classes, should be placed in dedicated files (`coordinator.py` and `entity.py`, respectively) to enhance consistency and maintainability.

This rule does not apply to the `local_todo` integration for the following reasons:

1.  **No Data Update Coordinator:** The `local_todo` integration manages its data (to-do list items) through `LocalTodoListStore` (defined in `store.py`), which interacts directly with a local ICS file. Data is loaded upon setup and modified through entity service calls (e.g., `async_create_todo_item`, `async_update_todo_item`). There is no periodic background fetching or centralized data update mechanism that would necessitate a `DataUpdateCoordinator` (or a similar custom coordinator) that would belong in `coordinator.py`. The data is local and updates are reactive to user actions.

2.  **Single Entity Type:** The integration defines only one platform, `Platform.TODO` (as seen in `__init__.py`), and consequently, only one entity type: `LocalTodoListEntity` (defined in `todo.py`). The `common-modules` rule suggests placing a *base entity* in `entity.py` when an integration provides multiple entity types that share common logic. Since `local_todo` has only `LocalTodoListEntity` which inherits directly from `homeassistant.components.todo.TodoListEntity`, there is no custom base entity within the integration that would serve multiple derived entity types.

Therefore, the patterns that `coordinator.py` and `entity.py` are intended to house are not present or applicable in the current design of the `local_todo` integration.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:27:10. Prompt tokens: 4983, Output tokens: 526, Total tokens: 7613_
