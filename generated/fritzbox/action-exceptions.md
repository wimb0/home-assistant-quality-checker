```markdown
# fritzbox: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions) |
| Status | **todo**                                                                 |

## Overview

The rule `action-exceptions` requires that Home Assistant service actions implemented by an integration should raise exceptions (`HomeAssistantError` or `ServiceValidationError`) when encountering failures. `ServiceValidationError` is for errors caused by incorrect input or usage, while `HomeAssistantError` is for errors during the execution of the service action, such as network issues or device communication problems.

This rule applies to the `fritzbox` integration as it implements various service actions through its entity platforms (e.g., `async_turn_on`, `async_set_temperature`, `async_press`).

The `fritzbox` integration partially follows this rule. It correctly implements raising `HomeAssistantError` for certain logical/state-based failures (e.g., attempting to control a device that is locked or in holiday/summer mode), as seen in `homeassistant/components/fritzbox/switch.py` and `homeassistant/components/fritzbox/climate.py`.

However, the integration does **not** consistently wrap potential operational errors (like communication failures with the FRITZ!Box) that might occur when executing library calls (`self.data.set_...` or `self.coordinator.fritz.apply_template`) via `self.hass.async_add_executor_job`. While `pyfritzhome` or the underlying `requests` library may raise exceptions (like `ConnectionError` or `HTTPError`), these exceptions are not explicitly caught and re-raised as `HomeAssistantError` within the service methods themselves. This means that users might see less user-friendly or specific error messages in the UI when a service action fails due to communication problems compared to the recommended `HomeAssistantError`.

For example, in `homeassistant/components/fritzbox/cover.py`, methods like `async_open_cover`, `async_close_cover`, `async_set_cover_position`, and `async_stop_cover` call `self.hass.async_add_executor_job(self.data.set_..., True)` without a `try...except` block to catch potential communication errors from the `pyfritzhome` library. The same pattern is observed in `homeassistant/components/fritzbox/light.py` and `homeassistant/components/fritzbox/button.py`, and for the library interaction calls within the methods in `homeassistant/components/fritzbox/climate.py` and `homeassistant/components/fritzbox/switch.py`.

## Suggestions

To fully comply with the `action-exceptions` rule, the `fritzbox` integration should ensure that potential operational errors during service action execution are caught and re-raised as `HomeAssistantError`.

This can be achieved by adding `try...except` blocks around the calls to `self.hass.async_add_executor_job` in the service methods of the entity platforms (`cover.py`, `light.py`, `button.py`, `climate.py`, `switch.py`).

**Example:**

In `homeassistant/components/fritzbox/cover.py`, the `async_open_cover` method could be updated as follows:

```python
# Before:
async def async_open_cover(self, **kwargs: Any) -> None:
    """Open the cover."""
    await self.hass.async_add_executor_job(self.data.set_blind_open, True)
    await self.coordinator.async_refresh()

# After:
from homeassistant.exceptions import HomeAssistantError
# Add imports for potential exceptions from pyfritzhome/requests if known
# from pyfritzhome import ...
# from requests.exceptions import ConnectionError as RequestConnectionError # Already imported in coordinator

async def async_open_cover(self, **kwargs: Any) -> None:
    """Open the cover."""
    try:
        await self.hass.async_add_executor_job(self.data.set_blind_open, True)
        # Catch potential pyfritzhome/requests errors here
    except Exception as err: # Catching a broad Exception for illustration, specific exceptions preferred
        raise HomeAssistantError(
            f"Failed to open cover {self.name}: {err}" # Or use translation keys for user messages
        ) from err

    await self.coordinator.async_refresh()

```

This pattern should be applied to all service methods that interact with the `pyfritzhome` library via the executor across the different platforms. The specific exceptions to catch might include `requests.exceptions.ConnectionError`, `requests.exceptions.HTTPError`, or potentially exceptions defined within the `pyfritzhome` library itself if they are indicative of operational failures. Re-raising as `HomeAssistantError` provides a consistent and user-friendly way for Home Assistant to report service failures.

_Created at 2025-05-25 11:34:17. Prompt tokens: 18984, Output tokens: 1147, Total tokens: 21419_
