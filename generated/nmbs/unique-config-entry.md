# nmbs: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [nmbs](https://www.home-assistant.io/integrations/nmbs/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `unique-config-entry` rule requires that an integration prevents the same device or service from being set up multiple times. This is typically achieved by assigning a unique ID to the configuration entry or by matching specific data fields to ensure uniqueness.

The `nmbs` integration uses a config flow (`manifest.json` specifies `config_flow: true`), so this rule applies.

The integration correctly implements this rule by assigning a unique ID to each configuration entry.
In `config_flow.py`, the `async_step_user` method constructs a `unique_id` based on the departure station ID, arrival station ID, and whether connections with transfers (vias) should be excluded:

```python
# config_flow.py
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # ...
        if user_input is not None:
            # ...
            else:
                # ...
                vias = "_excl_vias" if user_input.get(CONF_EXCLUDE_VIAS) else ""
                await self.async_set_unique_id(
                    f"{user_input[CONF_STATION_FROM]}_{user_input[CONF_STATION_TO]}{vias}"
                )
                self._abort_if_unique_id_configured() # This call aborts if the unique_id already exists
                # ...
                return self.async_create_entry(
                    title=config_entry_name,
                    data=user_input,
                )
        # ...
```

The key lines are `await self.async_set_unique_id(...)` followed by `self._abort_if_unique_id_configured()`. This ensures that if a configuration with the same combination of departure station, arrival station, and via preference already exists, the flow will abort, preventing duplicate entries.

This mechanism is also applied to configurations imported from YAML. The `async_step_import` method processes the YAML data and then calls `await self.async_step_user(user_input)`, thereby reusing the same uniqueness check:

```python
# config_flow.py
    async def async_step_import(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        # ... (data processing and conversion from names to IDs) ...
        return await self.async_step_user(user_input)
```

This implementation effectively prevents users from accidentally setting up the same NMBS route monitor multiple times, adhering to the `unique-config-entry` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:27:43. Prompt tokens: 12072, Output tokens: 704, Total tokens: 16708_
