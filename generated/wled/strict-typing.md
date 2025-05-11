# wled: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **todo**                                                                 |

## Overview

The `strict-typing` rule applies to all integrations to improve code quality and catch bugs early by leveraging Python's type hinting system. For integrations that implement `runtime-data` (i.e., store runtime information on the config entry, typically a coordinator), the rule has a specific mandate: "the use of a custom typed `MyIntegrationConfigEntry` is required and must be used throughout."

The `wled` integration correctly defines a custom typed config entry in `__init__.py`:
```python
# __init__.py
type WLEDConfigEntry = ConfigEntry[WLEDDataUpdateCoordinator]
```
And it uses `entry.runtime_data = WLEDDataUpdateCoordinator(hass, entry=entry)` to store the coordinator, thus falling under the `runtime-data` special requirement.

This `WLEDConfigEntry` type is used in many appropriate places, such as:
*   `async_setup_entry` in `__init__.py`.
*   `async_unload_entry` in `__init__.py`.
*   All platform `async_setup_entry` functions (e.g., `light.py`, `sensor.py`).
*   `async_get_config_entry_diagnostics` in `diagnostics.py`.

However, the requirement is that this custom typed `ConfigEntry` "must be used **throughout**". The `wled` integration does not fully adhere to this in the following instances:

1.  **`__init__.py`**:
    *   The `async_reload_entry` function signature uses the generic `ConfigEntry`:
        ```python
        async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
        ```
        It should use `WLEDConfigEntry`.

2.  **`config_flow.py`**:
    *   The `WLEDFlowHandler.async_get_options_flow` method signature uses the generic `ConfigEntry`:
        ```python
        @staticmethod
        @callback
        def async_get_options_flow(
            config_entry: ConfigEntry,
        ) -> WLEDOptionsFlowHandler:
        ```
        It should use `WLEDConfigEntry`.
    *   In `WLEDOptionsFlowHandler`, `self.config_entry` (inherited from `OptionsFlow`) is typed as the generic `ConfigEntry`. While the current options flow only accesses `self.config_entry.options` (which is fine), if it were to access `runtime_data`, explicit typing or casting to `WLEDConfigEntry` would be necessary.

3.  **`coordinator.py`**:
    *   The `WLEDDataUpdateCoordinator` class annotates its `config_entry` attribute and its `__init__` method's `entry` parameter with the generic `ConfigEntry`:
        ```python
        # coordinator.py
        class WLEDDataUpdateCoordinator(DataUpdateCoordinator[WLEDDevice]):
            # ...
            config_entry: ConfigEntry # Should be WLEDConfigEntry
            # ...
            def __init__(
                self,
                hass: HomeAssistant,
                *,
                entry: ConfigEntry, # Should be WLEDConfigEntry
            ) -> None:
                # ...
                self.config_entry = entry
        ```

These instances demonstrate that the custom `WLEDConfigEntry` is not used "throughout", leading to a "todo" status. General type hinting elsewhere in the integration (function arguments, return types, variable annotations) is largely in place and uses `from __future__ import annotations`.

## Suggestions

To make the `wled` integration compliant with the `strict-typing` rule, specifically the requirement for the custom `ConfigEntry` to be used "throughout":

1.  **In `__init__.py`:**
    *   Modify the signature of `async_reload_entry`:
        ```python
        # From
        async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
        # To
        async def async_reload_entry(hass: HomeAssistant, entry: WLEDConfigEntry) -> None:
        ```
    *   **Reason:** This ensures that if `entry.runtime_data` (which is of type `WLEDDataUpdateCoordinator`) is accessed within this function, its type is correctly known.

2.  **In `config_flow.py`:**
    *   Modify the signature of `WLEDFlowHandler.async_get_options_flow`:
        ```python
        # From
        def async_get_options_flow(
            config_entry: ConfigEntry,
        ) -> WLEDOptionsFlowHandler:
        # To
        def async_get_options_flow(
            config_entry: WLEDConfigEntry,
        ) -> WLEDOptionsFlowHandler:
        ```
    *   **Reason:** Consistent use of the specific typed config entry improves type safety.

3.  **In `coordinator.py`:**
    *   Modify the `WLEDDataUpdateCoordinator` class:
        *   Change the class attribute annotation:
            ```python
            # From
            config_entry: ConfigEntry
            # To
            config_entry: WLEDConfigEntry
            ```
        *   Change the `__init__` method's `entry` parameter type:
            ```python
            # From
            entry: ConfigEntry,
            # To
            entry: WLEDConfigEntry,
            ```
    *   **Reason:** The `WLEDDataUpdateCoordinator` is intrinsically linked to `WLEDConfigEntry` (as `entry.runtime_data` *is* an instance of this coordinator). Typing it correctly makes this relationship explicit and safer.

**Additional Recommendations (Best Practices):**

*   **Add to `.strict-typing` file:** Consider adding `wled` to the [`.strict-typing`](https://github.com/home-assistant/core/blob/dev/.strict-typing) file in the Home Assistant core repository. This will enable stricter mypy checks for the integration during Home Assistant's CI, helping to catch typing issues.
*   **Library Typing (PEP-561):** The rule recommends that the underlying library (`python-wled`) be fully typed and PEP-561 compliant (by including a `py.typed` file). While this is a recommendation for the library, it significantly enhances the effectiveness of static type checking for the integration. If the library is not already PEP-561 compliant, contributing type hints to it would be beneficial.

_Created at 2025-05-10 23:10:12. Prompt tokens: 20870, Output tokens: 1550, Total tokens: 26629_
