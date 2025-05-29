# jewish_calendar: async-dependency

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [async-dependency](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/async-dependency)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `async-dependency` rule requires that external library dependencies used by an integration should ideally be asynchronous (using `asyncio`) to avoid performance-costly context switching between the asyncio event loop and synchronous threads.

This rule applies to the `jewish_calendar` integration because it has an external dependency, `hdate`, as specified in its `manifest.json`:
```json
"requirements": ["hdate[astral]==1.1.0"],
```

The `hdate` library appears to be synchronous. This assessment is based on how the `jewish_calendar` integration interacts with it:

1.  In `homeassistant/components/jewish_calendar/__init__.py`, the instantiation of `hdate.Location` is wrapped with `hass.async_add_executor_job`:
    ```python
    location = await hass.async_add_executor_job(
        partial(
            Location,
            # ... arguments ...
        )
    )
    ```
    This is the standard Home Assistant pattern for calling blocking (synchronous) code from an asynchronous function, indicating that `hdate.Location()` is a blocking call.

2.  In several other places, functions and methods from the `hdate` library are called directly from `async` methods without `await` and without being wrapped in `hass.async_add_executor_job`. For example:
    *   In `homeassistant/components/jewish_calendar/service.py`, the `async def get_omer_count` service handler directly calls `HebrewDate.from_gdate(...)`, `Omer(...)`, and `omer.count_str()`.
        ```python
        async def get_omer_count(call: ServiceCall) -> ServiceResponse:
            # ...
            hebrew_date = HebrewDate.from_gdate(...) # Direct call
            # ...
            omer = Omer(date=hebrew_date, nusach=nusach) # Direct call
            return {
                "message": str(omer.count_str()), # Direct call
                # ...
            }
        ```
    *   In `homeassistant/components/jewish_calendar/sensor.py`, the `async def async_update_data` method calls `self.make_zmanim(today)`. The `make_zmanim` method is synchronous and directly instantiates `Zmanim(...)` from the `hdate` library.
        ```python
        # In JewishCalendarBaseSensor within sensor.py
        async def async_update_data(self) -> None:
            # ...
            today_times = self.make_zmanim(today) # make_zmanim is sync, calls hdate.Zmanim()

        # In JewishCalendarEntity within entity.py
        def make_zmanim(self, date: dt.date) -> Zmanim:
            return Zmanim( # Direct call to hdate.Zmanim
                date=date,
                location=self.data.location,
                # ...
            )
        ```
    If these `hdate` library calls are blocking (which is typical for calculation-heavy synchronous libraries), calling them directly from `async` functions would block the Home Assistant event loop. This usage pattern strongly suggests these parts of the `hdate` library are also synchronous.

Since the `hdate` library is synchronous, it does not meet the ideal condition set by the `async-dependency` rule, which aims for dependencies to be asyncio-native to enhance performance and code simplicity. Therefore, the integration does not currently follow this rule.

## Suggestions

To make the `jewish_calendar` integration compliant with the `async-dependency` rule, the `hdate` library itself would need to be refactored to support `asyncio`. This is a change primarily for the `hdate` library maintainers.

For the `jewish_calendar` integration maintainers, the following steps can be considered:

1.  **Engage with `hdate` Library Developers:**
    *   Open an issue or discussion with the maintainers of the `hdate` library to explore the possibility of creating an asyncio-native version or adding an async API. Explain the benefits for Home Assistant integrations and other asyncio-based applications.

2.  **Contribute to `hdate` (if feasible):**
    *   Offer to help with the refactoring effort. This would typically involve:
        *   Identifying CPU-bound calculations within `hdate` (e.g., `Location()`, `Zmanim()`, `HDateInfo()`, `Omer()` initializations or related methods) that might be lengthy.
        *   Modifying these parts of the `hdate` library to expose `async def` methods. Internally, these async methods could use `asyncio.to_thread` (Python 3.9+) or a similar mechanism to run the synchronous, CPU-bound code in a separate thread, thus not blocking the event loop, while still providing an awaitable interface.
        *   Example (conceptual change in `hdate`):
            ```python
            # hdate library (conceptual)
            import asyncio

            class Location:
                @classmethod
                async def create(cls, *args, **kwargs):
                    # Run synchronous constructor in a thread
                    return await asyncio.to_thread(cls._sync_create, *args, **kwargs)

                @classmethod
                def _sync_create(cls, *args, **kwargs):
                    # Original synchronous logic for Location(...)
                    instance = cls()
                    # ... setup instance ...
                    return instance

            # Home Assistant integration usage
            # location = await hdate.Location.create(...)
            ```

3.  **Explore Alternatives:**
    *   If refactoring `hdate` is not viable in the short term, investigate if alternative asyncio-native Python libraries for Jewish calendar calculations exist.
    *   As a more involved option, consider forking `hdate` to create an asyncio-compatible version specifically for Home Assistant or wider use.

By having an asyncio-native `hdate` library, the `jewish_calendar` integration could `await` its functions directly, leading to cleaner code and avoiding the overhead of `hass.async_add_executor_job` for every potentially blocking call, aligning with the goals of the `async-dependency` rule.

**Note:** While the `async-dependency` rule focuses on the library itself being async, it's also crucial that all calls to any synchronous library from async code are wrapped (e.g., using `await hass.async_add_executor_job(...)`). This is covered by the `sync-call-executor` rule. The current review identifies that some calls to `hdate` from async methods (e.g., in `service.py` and `sensor.py`) are not wrapped, which should be addressed regardless of this `async-dependency` rule.

_Created at 2025-05-29 08:34:28. Prompt tokens: 13153, Output tokens: 1632, Total tokens: 20275_
