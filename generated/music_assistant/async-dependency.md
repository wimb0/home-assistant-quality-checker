# music_assistant: strict-typing

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [strict-typing](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/strict-typing)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `strict-typing` rule applies to the `music_assistant` integration as it is a general code quality standard aimed at improving robustness by leveraging Python's type hinting system.

The integration utilizes `entry.runtime_data` to store instance-specific data, as seen in `homeassistant/components/music_assistant/__init__.py`:
```python
# homeassistant/components/music_assistant/__init__.py
# ...
@dataclass
class MusicAssistantEntryData:
    """Hold Mass data for the config entry."""

    mass: MusicAssistantClient
    listen_task: asyncio.Task

# ...
    # store the listen task and mass client in the entry data
    entry.runtime_data = MusicAssistantEntryData(mass, listen_task)
# ...
```
According to the `strict-typing` rule, if an integration implements `runtime-data`, "the use of a custom typed `MyIntegrationConfigEntry` is required and must be used throughout."

The `music_assistant` integration defines a custom typed `ConfigEntry` alias:
```python
# homeassistant/components/music_assistant/__init__.py
type MusicAssistantConfigEntry = ConfigEntry[MusicAssistantEntryData]
```
This `MusicAssistantConfigEntry` type is correctly used in some places, such as the `async_setup_entry` function in `__init__.py` and `media_player.py`:
```python
# homeassistant/components/music_assistant/__init__.py
async def async_setup_entry(
    hass: HomeAssistant, entry: MusicAssistantConfigEntry
) -> bool:
    # ...
```
```python
# homeassistant/components/music_assistant/media_player.py
async def async_setup_entry(
    hass: HomeAssistant,
    entry: MusicAssistantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    # ...
```

However, the integration does not use `MusicAssistantConfigEntry` "throughout" as required. Several functions in `homeassistant/components/music_assistant/__init__.py` still use the generic `ConfigEntry` type for parameters that represent the integration's config entry. This leads to `entry.runtime_data` being typed as `Any` in those contexts, undermining the benefits of strict typing for `runtime_data`.

Specifically, the following functions in `homeassistant/components/music_assistant/__init__.py` use `ConfigEntry` instead of `MusicAssistantConfigEntry`:
1.  `_client_listen`:
    ```python
    async def _client_listen(
        hass: HomeAssistant,
        entry: ConfigEntry, # Should be MusicAssistantConfigEntry
        mass: MusicAssistantClient,
        init_ready: asyncio.Event,
    ) -> None:
        # ...
    ```
2.  `async_unload_entry`:
    ```python
    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool: # Should be MusicAssistantConfigEntry
        # ...
        mass_entry_data: MusicAssistantEntryData = entry.runtime_data # runtime_data is Any here
        # ...
    ```
3.  `async_remove_config_entry_device`:
    ```python
    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry # Should be MusicAssistantConfigEntry
    ) -> bool:
        # ...
    ```

Because the custom typed `MusicAssistantConfigEntry` is not used consistently where `runtime_data` is (or might be implicitly) involved, the integration does not fully comply with the `strict-typing` rule.

## Suggestions

To make the `music_assistant` integration compliant with the `strict-typing` rule:

1.  **Update function signatures to use `MusicAssistantConfigEntry`:**
    Modify the function signatures in `homeassistant/components/music_assistant/__init__.py` for `_client_listen`, `async_unload_entry`, and `async_remove_config_entry_device` to use `MusicAssistantConfigEntry` instead of the generic `ConfigEntry`.

    **Example changes:**
    ```python
    # In homeassistant/components/music_assistant/__init__.py

    # ... (other imports and definitions) ...
    type MusicAssistantConfigEntry = ConfigEntry[MusicAssistantEntryData]
    # ...

    async def _client_listen(
        hass: HomeAssistant,
        entry: MusicAssistantConfigEntry,  # Changed from ConfigEntry
        mass: MusicAssistantClient,
        init_ready: asyncio.Event,
    ) -> None:
        # ...
    
    async def async_unload_entry(hass: HomeAssistant, entry: MusicAssistantConfigEntry) -> bool:  # Changed from ConfigEntry
        # runtime_data will now be correctly typed as MusicAssistantEntryData
        mass_entry_data = entry.runtime_data 
        # ...

    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: MusicAssistantConfigEntry, device_entry: dr.DeviceEntry  # Changed from ConfigEntry
    ) -> bool:
        # ...
    ```

2.  **Reasoning for changes:**
    These changes ensure that `entry.runtime_data` (or `config_entry.runtime_data`) is correctly typed as `MusicAssistantEntryData` in all relevant parts of the integration. This allows `mypy` to perform stricter checks and helps catch potential errors related to the structure or availability of data within `runtime_data`. This fulfills the requirement that the custom typed `ConfigEntry` "must be used throughout."

3.  **Enable strict type checking:**
    Once the code is fully typed and the above suggestions are implemented, consider adding the `music_assistant` integration to the `.strict-typing` file in the Home Assistant core repository. This will enable strict `mypy` checks for this integration during development and CI, helping to maintain a high level of type safety.

_Created at 2025-05-14 11:56:35. Prompt tokens: 29988, Output tokens: 1461, Total tokens: 36426_
