# local_todo: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `unique-config-entry` rule applies to the `local_todo` integration because it uses a config flow (`config_flow: true` in `manifest.json`) to allow users to set up instances of the integration. The rule mandates that an integration must prevent the same device or service from being set up multiple times to avoid duplicate entities and potential unique ID collisions.

The `local_todo` integration **fully follows** this rule. It achieves this by ensuring that each to-do list has a unique identifier derived from its name, which is then used to prevent duplicate configurations.

Specifically, in the `config_flow.py` file, during the `async_step_user` method, the integration performs the following steps:
1.  It prompts the user for a `CONF_TODO_LIST_NAME`.
2.  It generates a `key` by slugifying the provided list name: `key = slugify(user_input[CONF_TODO_LIST_NAME])`. This `key` is stored as `CONF_STORAGE_KEY` in the config entry data and is also used to determine the filename for the ICS file (e.g., `.storage/local_todo.{key}.ics`).
3.  It then explicitly checks for uniqueness using this `key`: `self._async_abort_entries_match({CONF_STORAGE_KEY: key})`.

This `_async_abort_entries_match` call checks if another config entry for the `local_todo` domain already exists with the same `CONF_STORAGE_KEY`. If a match is found, the config flow is aborted, preventing the user from creating a to-do list that would conflict with an existing one (e.g., by having the same name or a name that slugifies to the same key). This corresponds to the "Unique data" example implementation described in the rule.

```python
# homeassistant/components/local_todo/config_flow.py
# ...
class LocalTodoConfigFlow(ConfigFlow, domain=DOMAIN):
    # ...
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            key = slugify(user_input[CONF_TODO_LIST_NAME])
            # This line ensures that a config entry with the same storage key cannot be created.
            self._async_abort_entries_match({CONF_STORAGE_KEY: key})
            user_input[CONF_STORAGE_KEY] = key
            return self.async_create_entry(
                title=user_input[CONF_TODO_LIST_NAME], data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
# ...
```

The `strings.json` file also includes an abort reason for `already_configured`, which is typically used in conjunction with these uniqueness checks:
```json
{
  "config": {
    "abort": {
      "already_configured": "[%key:common::config_flow::abort::already_configured_service%]"
    }
  }
}
```
This mechanism effectively prevents the user from accidentally setting up the same to-do list (identified by its name/storage key) twice.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:33:48. Prompt tokens: 5695, Output tokens: 892, Total tokens: 8631_
