# local_calendar: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_calendar](https://www.home-assistant.io/integrations/local_calendar/) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not use a DataUpdateCoordinator and provides only a single entity type, so the specific patterns targeted by this rule (coordinator in `coordinator.py`, base entity for multiple types in `entity.py`) are not applicable. |

## Overview

The `common-modules` rule aims to increase consistency across integrations by standardizing the placement of common architectural patterns. Specifically, it mandates that:
1.  DataUpdateCoordinators should be placed in a `coordinator.py` file.
2.  Base entities, used to share common code when an integration provides multiple entity types, should be placed in an `entity.py` file.

This rule does **not apply** to the `local_calendar` integration. Here's why:

1.  **No DataUpdateCoordinator:**
    The `local_calendar` integration manages calendar data stored in local ICS files. It does not utilize Home Assistant's `DataUpdateCoordinator` pattern for fetching or polling data from an external source or for regular background updates.
    *   In `__init__.py`, the integration sets up a `LocalCalendarStore` (from `store.py`) to load and save the ICS file.
    *   The `LocalCalendarEntity` in `calendar.py` has an `async_update` method, but this method recalculates the next upcoming event from the already loaded calendar data rather than coordinating a new data fetch from a source.
    *   Updates to the calendar (creating, deleting, updating events) are typically triggered by service calls, which directly modify the stored ICS file and then prompt a state update.
    Since there is no `DataUpdateCoordinator`, the requirement to place it in `coordinator.py` is not applicable.

2.  **Single Entity Type / No Internal Base Entity for Multiple Types:**
    The `local_calendar` integration defines and exposes only one type of entity: `LocalCalendarEntity`, which is defined in `calendar.py`.
    The rule's guidance for an `entity.py` file is specifically for a "base entity" intended to "reduce code duplication" when "integrations provide more types of entities."
    *   `local_calendar` only provides the `calendar` platform (as seen in `PLATFORMS` in `__init__.py`).
    *   `LocalCalendarEntity` in `calendar.py` is the sole, concrete entity class for this integration. It does not serve as a base class for other entity types *within the `local_calendar` integration itself* (e.g., there are no sensors or switches for this integration that would inherit from a common base).
    Therefore, the motivation and requirement for a base entity in `entity.py` (as described by the rule for handling multiple entity types and reducing duplication) do not apply to this integration's structure.

Given that `local_calendar` does not employ a DataUpdateCoordinator and does not have a scenario requiring an internal base entity for multiple entity types, the specific structural conventions promoted by the `common-modules` rule are not relevant to its current design. Thus, the integration is considered exempt from this rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:23:13. Prompt tokens: 6358, Output tokens: 779, Total tokens: 12356_
