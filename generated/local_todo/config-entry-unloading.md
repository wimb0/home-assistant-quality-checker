# local_todo: config-entry-unloading

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [local_todo](https://www.home-assistant.io/integrations/local_todo/) |
| Rule   | [config-entry-unloading](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `config-entry-unloading` rule requires that integrations support unloading their configuration entries at runtime. This allows Home Assistant to remove or reload the integration without a full restart, improving user experience.

This rule applies to the `local_todo` integration because it uses config entries, as indicated by `config_flow: true` in its `manifest.json` and the presence of `async_setup_entry` and `async_unload_entry` functions in `__init__.py`.

The `local_todo` integration **follows** this rule.

1.  **Implementation of `async_unload_entry`**:
    The integration correctly implements the `async_unload_entry` function in `homeassistant/components/local_todo/__init__.py`:
    ```python
    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Unload a config entry."""
        return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    ```
    This function calls `hass.config_entries.async_unload_platforms(entry, PLATFORMS)`, which is the standard and correct way to unload any platforms (in this case, the `todo` platform) that were set up for this config entry.

2.  **Resource Management in `async_setup_entry`**:
    In `async_setup_entry`, the integration performs the following key actions:
    ```python
    # homeassistant/components/local_todo/__init__.py
    async def async_setup_entry(hass: HomeAssistant, entry: LocalTodoConfigEntry) -> bool:
        """Set up Local To-do from a config entry."""
        path = Path(hass.config.path(STORAGE_PATH.format(key=entry.data[CONF_STORAGE_KEY])))
        store = LocalTodoListStore(hass, path)
        try:
            await store.async_load()
        except OSError as err:
            raise ConfigEntryNotReady("Failed to load file {path}: {err}") from err

        entry.runtime_data = store

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        return True
    ```
    -   It initializes a `LocalTodoListStore` instance, which is responsible for loading and saving todo list data from/to an `.ics` file. This `store` is then placed into `entry.runtime_data`.
    -   It then calls `hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)` to set up the associated `todo` platform.

3.  **Cleanup of Resources**:
    The rule emphasizes cleaning up subscriptions and closing connections.
    -   The `LocalTodoListStore` (from `store.py`) primarily manages file I/O and uses an `asyncio.Lock`. It does not establish persistent network connections, subscribe to event bus events, or create background tasks like `DataUpdateCoordinator`s that would require explicit cleanup in `__init__.py`'s `async_unload_entry` beyond what `async_unload_platforms` handles.
    -   File operations within `LocalTodoListStore` (e.g., `_path.read_text()`, `_path.write_text()`) are self-contained and do not leave file handles open at the instance level.
    -   The `asyncio.Lock` within the store will be garbage collected along with the store instance when it's no longer referenced after the entry is unloaded.
    -   Any resources managed by the `todo` platform entities (like the `LocalTodoListEntity`) are handled by the platform unloading mechanism initiated by `async_unload_platforms`.

Since `async_setup_entry` does not create resources that live independently of the platforms it sets up, or resources that require explicit teardown beyond standard garbage collection (like the `store` object itself once all references are gone), the call to `async_unload_platforms` in `async_unload_entry` is sufficient to meet the rule's requirements. The integration does not have other listeners or connections directly managed by `__init__.py` that would need to be cleaned up as shown in the rule's example (`entry.runtime_data.listener()`).

Therefore, the integration correctly handles config entry unloading.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 23:35:58. Prompt tokens: 5093, Output tokens: 1078, Total tokens: 11495_
