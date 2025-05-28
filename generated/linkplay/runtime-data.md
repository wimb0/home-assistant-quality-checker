# linkplay: runtime-data

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [runtime-data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `runtime-data` rule mandates the use of `ConfigEntry.runtime_data` for storing data that is needed during the lifetime of a configuration entry but is not persisted to configuration storage. It also encourages extending the `ConfigEntry` type for better type safety.

The `linkplay` integration adheres to this rule.

1.  **Typed ConfigEntry and Data Structure:**
    In `__init__.py`, the integration defines a `dataclass` named `LinkPlayData` to structure the runtime data. It then creates a type alias `LinkPlayConfigEntry` for `ConfigEntry[LinkPlayData]`:
    ```python
    # __init__.py
    @dataclass
    class LinkPlayData:
        """Data for LinkPlay."""

        bridge: LinkPlayBridge


    type LinkPlayConfigEntry = ConfigEntry[LinkPlayData]
    ```
    This establishes a clear, typed structure for the data stored in `runtime_data`.

2.  **Storing Data in `runtime_data`:**
    Within the `async_setup_entry` function in `__init__.py`, an instance of `LinkPlayBridge` (which is runtime-specific data) is created and then stored in `entry.runtime_data` wrapped by the `LinkPlayData` class:
    ```python
    # __init__.py
    async def async_setup_entry(hass: HomeAssistant, entry: LinkPlayConfigEntry) -> bool:
        # ...
        bridge = await linkplay_factory_httpapi_bridge(entry.data[CONF_HOST], session)
        # ...
        entry.runtime_data = LinkPlayData(bridge=bridge)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    ```
    This correctly places the runtime `bridge` object into `entry.runtime_data`.

3.  **Accessing `runtime_data`:**
    The integration consistently uses the typed `LinkPlayConfigEntry` and accesses `runtime_data` where needed:
    *   In `async_unload_entry` (`__init__.py`):
        ```python
        bridge: LinkPlayBridge | None = entry.runtime_data.bridge
        ```
    *   In platform setup functions, for example, `button.py`:
        ```python
        # button.py
        async def async_setup_entry(
            hass: HomeAssistant,
            config_entry: LinkPlayConfigEntry,
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            """Set up the LinkPlay buttons from config entry."""
            async_add_entities(
                LinkPlayButton(config_entry.runtime_data.bridge, description)
                for description in BUTTON_TYPES
            )
        ```
    *   Similarly in `media_player.py`:
        ```python
        # media_player.py
        async def async_setup_entry(
            hass: HomeAssistant,
            entry: LinkPlayConfigEntry,
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            # ...
            async_add_entities([LinkPlayMediaPlayerEntity(entry.runtime_data.bridge)])
        ```
    *   And in `diagnostics.py`:
        ```python
        # diagnostics.py
        async def async_get_config_entry_diagnostics(
            hass: HomeAssistant, entry: LinkPlayConfigEntry
        ) -> dict[str, Any]:
            data = entry.runtime_data
            return {"device_info": data.bridge.to_dict()}
        ```

The `linkplay` integration correctly utilizes `entry.runtime_data` to store its per-entry `LinkPlayBridge` instance and employs a typed `ConfigEntry` for improved code clarity and safety, thus fully complying with the `runtime-data` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:12:14. Prompt tokens: 10599, Output tokens: 985, Total tokens: 13907_
