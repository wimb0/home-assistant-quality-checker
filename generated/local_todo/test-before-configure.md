# local_todo: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `test-before-configure` rule requires integrations to validate user input and test any necessary connections or resource accessibility during the config flow, *before* the configuration entry is created. This is to provide immediate feedback to the user about potential issues like incorrect permissions, invalid paths, or unreachable services.

This rule applies to the `local_todo` integration because it interacts with the local filesystem to store and manage to-do lists in `.ics` files. Potential issues include the storage directory not being writable or an existing file not being readable by Home Assistant. These are the types of issues the rule aims to catch early.

The `local_todo` integration currently does **not** follow this rule.
In `config_flow.py`, the `async_step_user` method takes the desired to-do list name, generates a storage key, and then directly proceeds to `self.async_create_entry(...)` without performing any checks on the filesystem.

```python
# homeassistant/components/local_todo/config_flow.py
# ...
class LocalTodoConfigFlow(ConfigFlow, domain=DOMAIN):
    # ...
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            key = slugify(user_input[CONF_TODO_LIST_NAME])
            self._async_abort_entries_match({CONF_STORAGE_KEY: key})
            user_input[CONF_STORAGE_KEY] = key
            # No validation of filesystem access before creating the entry
            return self.async_create_entry(
                title=user_input[CONF_TODO_LIST_NAME], data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
```

While `async_setup_entry` in `__init__.py` does attempt to load the file and raises `ConfigEntryNotReady` if an `OSError` occurs, this happens *after* the config entry has been created, which is too late according to the rule. The rule's intent is to perform these checks within the config flow itself and display errors to the user directly in the setup form.

## Suggestions

To make the `local_todo` integration compliant with the `test-before-configure` rule, you should add validation steps within the `async_step_user` method in `config_flow.py`. These steps should check if Home Assistant can interact with the target file path for the to-do list.

Specifically, you should:
1.  Determine the full path to the `.ics` file that will be created or used.
2.  Check if the parent directory (typically `.storage/` within the Home Assistant configuration directory) is writable by Home Assistant. This is crucial for creating new list files and updating existing ones.
3.  If the `.ics` file already exists (e.g., user re-adding a previously configured list, or a manually placed file that isn't yet managed by a config entry), check if it's readable by Home Assistant.
4.  If any of these checks fail, populate the `errors` dictionary and return `self.async_show_form(...)` to display an appropriate error message to the user, preventing the creation of a non-functional config entry.

Here's an example of how you could modify `config_flow.py`:

```python
"""Config flow for Local To-do integration."""

from __future__ import annotations

import logging
import os # Required for os.access
from pathlib import Path # Required for Path object
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant # For type hinting hass
from homeassistant.util import slugify

from .const import CONF_STORAGE_KEY, CONF_TODO_LIST_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TODO_LIST_NAME): str,
    }
)

# Define new error constants (these would also need to be added to strings.json)
ERROR_STORAGE_NOT_WRITABLE = "storage_not_writable"
ERROR_FILE_NOT_READABLE = "file_not_readable"
ERROR_PATH_VALIDATION_FAILED = "path_validation_failed"


class LocalTodoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Local To-do."""

    VERSION = 1

    async def _validate_storage_path(self, hass: HomeAssistant, key: str) -> dict[str, str]:
        """Validate the storage path for the given key."""
        errors: dict[str, str] = {}
        # Path is constructed similarly to __init__.py:
        # STORAGE_PATH = ".storage/local_todo.{key}.ics"
        # path = Path(hass.config.path(STORAGE_PATH.format(key=key)))
        final_path = Path(hass.config.path(f".storage/local_todo.{key}.ics"))
        storage_dir = final_path.parent

        try:
            # Test 1: Ensure the parent directory (.storage) is writable.
            is_storage_writable = await hass.async_add_executor_job(
                os.access, storage_dir, os.W_OK
            )
            if not is_storage_writable:
                _LOGGER.error(
                    "The storage directory '%s' is not writable by Home Assistant.",
                    storage_dir,
                )
                errors["base"] = ERROR_STORAGE_NOT_WRITABLE
                return errors # Stop further checks if directory isn't writable

            # Test 2: If the file already exists, check if it's readable.
            # This happens after _async_abort_entries_match, so an existing file
            # here implies it's not managed by another HA config entry.
            file_exists = await hass.async_add_executor_job(final_path.exists)
            if file_exists:
                is_file_readable = await hass.async_add_executor_job(
                    os.access, final_path, os.R_OK
                )
                if not is_file_readable:
                    _LOGGER.error(
                        "The existing todo file '%s' is not readable by Home Assistant.",
                        final_path,
                    )
                    errors["base"] = ERROR_FILE_NOT_READABLE
            # else:
                # Optional: If file does not exist, could try a "touch" or temporary write
                # to ensure file *can* be created, though directory writability covers most of this.
                # For example, await hass.async_add_executor_job(final_path.touch, exist_ok=True)
                # and then await hass.async_add_executor_job(final_path.unlink, missing_ok=True)
                # This might be overkill if os.access(storage_dir, os.W_OK) is sufficient.

        except OSError as e:
            _LOGGER.error("Error accessing or validating storage path %s: %s", final_path, e)
            errors["base"] = ERROR_PATH_VALIDATION_FAILED
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected exception during storage path validation")
            errors["base"] = "unknown" # Standard HA error
        
        return errors


    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            key = slugify(user_input[CONF_TODO_LIST_NAME])
            
            # Prevent duplicate config entries for the same storage key
            self._async_abort_entries_match({CONF_STORAGE_KEY: key})

            # Perform validation checks before creating the entry
            errors = await self._validate_storage_path(self.hass, key)

            if not errors:
                user_input[CONF_STORAGE_KEY] = key
                return self.async_create_entry(
                    title=user_input[CONF_TODO_LIST_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

```

**Additionally:**
*   You would need to add the new error keys (`storage_not_writable`, `file_not_readable`, `path_validation_failed`) and their corresponding user-friendly messages to the `strings.json` file for this integration. For example:
    ```json
    // homeassistant/components/local_todo/strings.json
    {
      // ... existing content ...
      "errors": {
        "storage_not_writable": "The Home Assistant storage directory is not writable. Please check permissions.",
        "file_not_readable": "An existing to-do list file was found but is not readable. Please check its permissions.",
        "path_validation_failed": "There was an error validating the storage path for the to-do list. Check logs for details."
      }
    }
    ```

These changes would ensure that potential filesystem issues are caught during the configuration phase, providing a better user experience and aligning the integration with the `test-before-configure` quality scale rule.

_Created at 2025-05-28 23:31:30. Prompt tokens: 5278, Output tokens: 2315, Total tokens: 12905_
