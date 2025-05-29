# local_todo: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-setup` rule requires that an integration, during its initialization (`async_setup_entry` in `__init__.py`), checks if it can be set up correctly and raises specific exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`) if not. This ensures users are immediately informed of setup issues.

This rule applies to the `local_todo` integration as it uses config entries and implements `async_setup_entry` in `homeassistant/components/local_todo/__init__.py`.

The integration currently **partially follows** this rule, leading to a "todo" status.
Specifically, in `homeassistant/components/local_todo/__init__.py`, the `async_setup_entry` function (lines 18-30) attempts to load the to-do list data from an `.ics` file:
```python
    # __init__.py L20-L25
    path = Path(hass.config.path(STORAGE_PATH.format(key=entry.data[CONF_STORAGE_KEY])))
    store = LocalTodoListStore(hass, path)
    try:
        await store.async_load()
    except OSError as err:
        raise ConfigEntryNotReady(f"Failed to load file {path}: {err}") from err
```
This code correctly handles `OSError` exceptions (e.g., file not found, permission issues) by raising `ConfigEntryNotReady`, which is appropriate for temporary issues that might be resolved on a retry.

However, it does not check for issues related to the *content* of the `.ics` file. If the file is accessible (no `OSError`) but contains malformed or unparseable ICS data, `store.async_load()` will successfully return this data as a string. The main `async_setup_entry` in `__init__.py` will then complete successfully. The parsing error would only occur later, during the platform setup in `homeassistant/components/local_todo/todo.py` (lines 45-51):
```python
    # todo.py L45-L51
    store = config_entry.runtime_data
    ics = await store.async_load()

    with async_pause_setup(hass, SetupPhases.WAIT_IMPORT_PACKAGES):
        calendar: Calendar = await hass.async_add_import_executor_job(
            IcsCalendarStream.calendar_from_ics, ics
        )
```
If `IcsCalendarStream.calendar_from_ics` fails here due to invalid content, the config entry will already be marked as loaded, but the associated entities will fail to set up. This does not align with the rule's intent to "immediately let the user know that it doesn't work" at the integration setup level. A corrupted ICS file represents a non-temporary issue that prevents the integration from working correctly and should ideally raise a `ConfigEntryError` from `__init__.py`.

## Suggestions

To make the `local_todo` integration compliant with the `test-before-setup` rule, the `async_setup_entry` function in `homeassistant/components/local_todo/__init__.py` should be enhanced to validate the content of the `.ics` file. This involves attempting to parse the ICS data and raising `ConfigEntryError` if parsing fails due to malformed content.

Here's how you can modify `homeassistant/components/local_todo/__init__.py`:

1.  **Import necessary modules:**
    ```python
    import logging # Add this
    from ical.calendar_stream import IcsCalendarStream # Add this
    # from ical.some_specific_parser_error import ParserError # If applicable, or use ValueError
    from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryError # Add ConfigEntryError
    from homeassistant.setup import SetupPhases, async_pause_setup # Add these
    ```

2.  **Add a logger instance:**
    ```python
    _LOGGER = logging.getLogger(__name__) # Add this
    ```

3.  **Modify `async_setup_entry` to include parsing and error handling:**
    ```python
    async def async_setup_entry(hass: HomeAssistant, entry: LocalTodoConfigEntry) -> bool:
        """Set up Local To-do from a config entry."""
        path = Path(hass.config.path(STORAGE_PATH.format(key=entry.data[CONF_STORAGE_KEY])))
        store = LocalTodoListStore(hass, path)
        try:
            ics_content = await store.async_load()
            if ics_content:  # Only attempt to parse if there is content
                # Attempt to parse the ICS content to validate it.
                # This ensures that if the file is corrupt, we fail early during entry setup.
                # The ical library might dynamically load packages on its first run.
                with async_pause_setup(hass, SetupPhases.WAIT_IMPORT_PACKAGES):
                    await hass.async_add_import_executor_job(
                        IcsCalendarStream.calendar_from_ics, ics_content
                    )
        except OSError as err:
            _LOGGER.warning("Failed to load .ics file %s: %s", path, err)
            raise ConfigEntryNotReady(f"Failed to load .ics file {path}: {err}") from err
        except ValueError as err:  # Catch ValueError if ical library raises it for parsing errors
            _LOGGER.error("Failed to parse .ics file %s due to invalid content: %s", path, err)
            raise ConfigEntryError(
                f"The .ics file at {path} is corrupted or has an invalid format. "
                "Please check the file content."
            ) from err
        except Exception as err:  # Catch other potential parsing-related exceptions
            _LOGGER.error("Unexpected error processing .ics file %s: %s", path, err, exc_info=True)
            raise ConfigEntryError(
                f"An unexpected error occurred while processing the .ics file at {path}."
            ) from err

        entry.runtime_data = store
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    ```

**Explanation of Changes:**

*   The `ics_content` is loaded from the store.
*   If `ics_content` is not empty, `IcsCalendarStream.calendar_from_ics` is called within `hass.async_add_import_executor_job` to attempt parsing. This is similar to how it's done in `todo.py` and includes `async_pause_setup` because the `ical` library might dynamically load packages.
*   `OSError` is still caught and raises `ConfigEntryNotReady` as before.
*   `ValueError` (a common exception for parsing errors, which `python-ical` might raise) is caught. If such an error occurs, it indicates corrupted or invalid ICS data. `ConfigEntryError` is raised, clearly informing the user that the setup failed due to a persistent issue with the file content.
*   A general `Exception` catch-all is added for other unexpected parsing issues, also raising `ConfigEntryError`.
*   Logging is added for better diagnostics.

By implementing these changes, the integration will perform a more comprehensive check during initialization. If the `.ics` file is unreadable (`OSError`) or its content is unparseable (e.g., `ValueError`), the appropriate `ConfigEntry` exception will be raised from `__init__.py`, immediately informing the user and adhering to the `test-before-setup` rule. This prevents the scenario where the config entry appears to load successfully but the entities fail to materialize due to bad data.

_Created at 2025-05-28 23:33:17. Prompt tokens: 5121, Output tokens: 1853, Total tokens: 15506_
