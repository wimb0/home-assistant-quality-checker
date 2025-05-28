# overkiz: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **todo**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `action-exceptions` rule requires that service actions raise appropriate exceptions (`ServiceValidationError` for incorrect user input, `HomeAssistantError` for other failures) when they encounter problems.

This rule applies to the `overkiz` integration as it implements numerous entities that provide services (e.g., covers, lights, climate, scenes).

The integration largely follows the requirement to raise `HomeAssistantError` for failures during API communication. Most service calls within the various entity platforms (cover, light, climate, etc.) delegate to `OverkizExecutor.async_execute_command` (defined in `homeassistant/components/overkiz/executor.py`). This central method includes a `try...except` block that catches `pyoverkiz.exceptions.BaseOverkizException` and re-raises it as `homeassistant.exceptions.HomeAssistantError`:

```python
# homeassistant/components/overkiz/executor.py
# OverkizExecutor.async_execute_command
            # ...
            try:
                exec_id = await self.coordinator.client.execute_command(
                    self.device.device_url,
                    Command(command_name, parameters),
                    "Home Assistant",
                )
            # Catch Overkiz exceptions to support `continue_on_error` functionality
            except BaseOverkizException as exception:
                raise HomeAssistantError(exception) from exception
            # ...
```
This ensures that errors from the `pyoverkiz` library (e.g., network issues, device rejections, API errors) are surfaced to the user as Home Assistant errors.

However, there is at least one instance where a service action directly calls the `pyoverkiz` client without this exception wrapping:
*   In `homeassistant/components/overkiz/scene.py`, the `OverkizScene.async_activate` method calls `self.client.execute_scenario(self.scenario.oid)` directly. The `execute_scenario` method in `pyoverkiz` can raise `OverkizException` (a subclass of `BaseOverkizException`). If this occurs, the exception is not currently caught and re-raised as a `HomeAssistantError`, meaning the failure might not be cleanly reported to the user through Home Assistant's standard error handling for services.

```python
# homeassistant/components/overkiz/scene.py
# OverkizScene.async_activate
    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self.client.execute_scenario(self.scenario.oid) # Potential unhandled OverkizException
```

Regarding `ServiceValidationError`: The integration does not explicitly raise `ServiceValidationError` for invalid user input within its service handlers. Much of the basic input validation (e.g., type checking, simple range constraints for numbers if defined in entity descriptions) is handled by Home Assistant Core before the service method is invoked. For device-specific invalid inputs or unsupported operations, the `pyoverkiz` library would typically raise an exception, which is then (usually) converted to `HomeAssistantError`. Given the direct nature of most Overkiz commands, this approach is generally acceptable, as the distinction between "user input error" and "device rejected valid-looking input" can be blurry at the `pyoverkiz` library level. The primary issue is ensuring *an* appropriate Home Assistant exception is raised, which is mostly handled except for the scene activation.

Due to the missing exception handling in `scene.py`, the integration does not fully follow the `action-exceptions` rule.

## Suggestions

To make the `overkiz` integration compliant with the `action-exceptions` rule, the following change should be made:

1.  **Modify `OverkizScene.async_activate` in `homeassistant/components/overkiz/scene.py`:**
    Wrap the call to `self.client.execute_scenario` in a `try...except` block to catch potential exceptions from the `pyoverkiz` library and re-raise them as `HomeAssistantError`.

    **Current Code:**
    ```python
    # homeassistant/components/overkiz/scene.py
    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self.client.execute_scenario(self.scenario.oid)
    ```

    **Suggested Change:**
    ```python
    # homeassistant/components/overkiz/scene.py
    from pyoverkiz.exceptions import BaseOverkizException # Or OverkizException if more specific
    from homeassistant.exceptions import HomeAssistantError

    # ... (inside OverkizScene class)

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        try:
            await self.client.execute_scenario(self.scenario.oid)
        except BaseOverkizException as err:
            # Consider a more specific message if desired, e.g., including self.name or self.scenario.label
            raise HomeAssistantError(
                f"Failed to activate scene '{self.name}': {err}"
            ) from err
    ```

    **Why this change satisfies the rule:**
    This change ensures that if `self.client.execute_scenario` (a `pyoverkiz` library call) fails and raises an exception (e.g., `OverkizException`), it will be caught. The caught exception will then be wrapped in a `HomeAssistantError`, which is the appropriate exception type for service action failures not caused by incorrect user input, as specified by the rule. This makes the error handling consistent with other service calls in the `overkiz` integration that go through `OverkizExecutor`.

_Created at 2025-05-28 12:17:51. Prompt tokens: 86993, Output tokens: 1399, Total tokens: 95686_
