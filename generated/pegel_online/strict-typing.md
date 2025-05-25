```markdown
# pegel_online: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **done**                                                                 |

## Overview

The `strict-typing` rule requires integrations to use type hints consistently throughout their Python code to catch potential bugs early via static analysis tools like `mypy`. It also recommends that any associated library be PEP-561 compliant and that the integration itself be added to the Home Assistant core's `.strict-typing` file to enforce strict checks. Furthermore, if the integration implements `runtime-data`, a custom typed `ConfigEntry` is mandatory.

Based on the provided code files for the `pegel_online` integration (`__init__.py`, `entity.py`, `coordinator.py`, `config_flow.py`, `sensor.py`, `diagnostics.py`), the integration demonstrates consistent and correct use of type hints.

Specifically:
*   All Python files that contain code (`__init__.py`, `entity.py`, `coordinator.py`, `config_flow.py`, `sensor.py`, `diagnostics.py`) heavily utilize type hints for function/method arguments, return types, and variable annotations.
*   The integration uses `runtime_data` (`__init__.py` assigns the coordinator to `entry.runtime_data`).
*   The integration correctly implements the requirement for `runtime-data` by defining and using a custom typed `ConfigEntry` alias: `type PegelOnlineConfigEntry = ConfigEntry[PegelOnlineDataUpdateCoordinator]` in `coordinator.py`. This custom type is then used consistently in `__init__.py`, `coordinator.py`, `sensor.py`, and `diagnostics.py` for the `config_entry` parameter/attribute.

While the provided files do not include the associated `aiopegelonline` library or the Home Assistant core `.strict-typing` file (which are external to the integration's component directory), the *integration code itself* fully adheres to the typing requirements and patterns expected for strict typing compliance within the Home Assistant framework, including the specific requirement for `runtime-data`. The code is ready for strict type checking.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:26:40. Prompt tokens: 5769, Output tokens: 548, Total tokens: 8196_
