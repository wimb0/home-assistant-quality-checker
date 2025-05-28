# overkiz: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **done**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `strict-typing` rule applies to the `overkiz` integration. This rule emphasizes the use of type hints to catch bugs early and improve code quality, especially by enabling strict type checks through tools like `mypy`. A key requirement is that if an integration implements `runtime-data`, it must use a custom typed `ConfigEntry`.

The `overkiz` integration **fully follows** this rule.

1.  **Use of `runtime-data` and Custom Typed `ConfigEntry`**:
    The integration utilizes `runtime_data` to store coordinator instances and other shared data. As per the rule's warning, this necessitates a custom typed `ConfigEntry`.
    In `homeassistant/components/overkiz/__init__.py`, this is correctly implemented:
    ```python
    from homeassistant.config_entries import ConfigEntry
    # ...

    @dataclass
    class HomeAssistantOverkizData:
        """Overkiz data stored in the runtime data object."""

        coordinator: OverkizDataUpdateCoordinator
        platforms: defaultdict[Platform, list[Device]]
        scenarios: list[Scenario]

    type OverkizDataConfigEntry = ConfigEntry[HomeAssistantOverkizData]

    async def async_setup_entry(hass: HomeAssistant, entry: OverkizDataConfigEntry) -> bool:
        # ...
        entry.runtime_data = HomeAssistantOverkizData(
            coordinator=coordinator, platforms=platforms, scenarios=scenarios
        )
        # ...
    ```
    The `OverkizDataConfigEntry` (which is `ConfigEntry[HomeAssistantOverkizData]`) is defined and used as the type hint for the `entry` parameter in `async_setup_entry`. This custom typed `ConfigEntry` is also consistently used throughout other relevant parts of the integration, such as in the `async_setup_entry` functions of its platforms (e.g., `sensor.py`, `light.py`, `climate/__init__.py`) and in `diagnostics.py`.

2.  **Comprehensive Type Hinting**:
    A review of the provided code files shows that type hints are used extensively for function arguments, return values, and variables. This practice is in line with the rule's goal of improving code robustness through static typing. Examples include:
    *   `hass: HomeAssistant`
    *   `client: OverkizClient | None`
    *   `devices: list[Device]`
    *   Return types like `-> bool`, `-> None`, `-> dict[str, Device]`.
    *   `from __future__ import annotations` is used in all Python files, facilitating modern type hinting.

The codebase is structured in a way that supports and is ready for strict type checking as enforced by Home Assistant's CI/CD pipeline (e.g., by being listed in the `.strict-typing` file).

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:49:58. Prompt tokens: 86873, Output tokens: 771, Total tokens: 91221_
