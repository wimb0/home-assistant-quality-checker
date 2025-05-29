# jewish_calendar: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule requires integrations to use the `ConfigEntry.runtime_data` attribute for storing runtime data and to do so in a typed manner, typically by defining a custom `ConfigEntry` type.

This rule applies to the `jewish_calendar` integration as it needs to store and manage data that is determined or processed at runtime, such as the `hdate.Location` object and various configuration parameters (offsets, language, diaspora status) that are used by entities during their lifetime.

The `jewish_calendar` integration fully follows this rule. It correctly utilizes `ConfigEntry.runtime_data` and ensures this data is properly typed.

**Evidence of Compliance:**

1.  **Typed Runtime Data Structure (`JewishCalendarData`):**
    In `homeassistant/components/jewish_calendar/entity.py`, a `dataclass` named `JewishCalendarData` is defined to hold all runtime information:
    ```python
    # homeassistant/components/jewish_calendar/entity.py
    @dataclass
    class JewishCalendarData:
        """Jewish Calendar runtime dataclass."""

        language: Language
        diaspora: bool
        location: Location
        candle_lighting_offset: int
        havdalah_offset: int
        results: JewishCalendarDataResults | None = None
    ```

2.  **Custom Typed `ConfigEntry` (`JewishCalendarConfigEntry`):**
    The integration defines a specific type for its config entries, associating it with `JewishCalendarData`. This is done in `homeassistant/components/jewish_calendar/entity.py`:
    ```python
    # homeassistant/components/jewish_calendar/entity.py
    type JewishCalendarConfigEntry = ConfigEntry[JewishCalendarData]
    ```
    This ensures that `config_entry.runtime_data` is typed as `JewishCalendarData`.

3.  **Usage in `async_setup_entry`:**
    In `homeassistant/components/jewish_calendar/__init__.py`, the `async_setup_entry` function correctly uses the `JewishCalendarConfigEntry` type and assigns an instance of `JewishCalendarData` to `config_entry.runtime_data`:
    ```python
    # homeassistant/components/jewish_calendar/__init__.py
    from .entity import JewishCalendarConfigEntry, JewishCalendarData # Import custom types

    async def async_setup_entry(
        hass: HomeAssistant, config_entry: JewishCalendarConfigEntry # Use custom ConfigEntry type
    ) -> bool:
        # ... (data retrieval) ...

        config_entry.runtime_data = JewishCalendarData( # Assign typed data
            language,
            diaspora,
            location,
            candle_lighting_offset,
            havdalah_offset,
        )
        # ...
        return True
    ```

4.  **Typed Access in Entities and Other Modules:**
    Entities and other parts of the integration (like diagnostics) consistently use the `JewishCalendarConfigEntry` type, ensuring that when `config_entry.runtime_data` is accessed, its type is known. For example, in `homeassistant/components/jewish_calendar/entity.py`:
    ```python
    # homeassistant/components/jewish_calendar/entity.py
    class JewishCalendarEntity(Entity):
        # ...
        def __init__(
            self,
            config_entry: JewishCalendarConfigEntry, # Use custom ConfigEntry type
            description: EntityDescription,
        ) -> None:
            # ...
            self.data = config_entry.runtime_data # self.data is implicitly typed as JewishCalendarData
            # ...
    ```
    Similarly, `diagnostics.py` and `config_flow.py` also use `JewishCalendarConfigEntry` for type hinting `config_entry` arguments where `runtime_data` might be relevant.

These practices align perfectly with the rule's example and intent, promoting typed, consistent storage of runtime data.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:08:25. Prompt tokens: 13426, Output tokens: 1006, Total tokens: 17216_
