# open_epaper_link: common-modules

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [common-modules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/common-modules)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `common-modules` rule states that common Home Assistant patterns, specifically data coordinators and base entities, should be placed in designated files (`coordinator.py` and `entity.py`, respectively) to improve consistency and code navigability.

This rule applies to the `open_epaper_link` integration for the following reasons:

1.  **Coordinator Pattern:** The integration uses a central class, `Hub`, defined in `open_epaper_link/hub.py`. This `Hub` class is responsible for managing the WebSocket connection to the OpenEPaperLink Access Point, fetching data, tracking tag states, and dispatching updates to entities. This role is analogous to the `DataUpdateCoordinator` pattern mentioned in the rule, even though `Hub` does not inherit from `DataUpdateCoordinator`. The rule's intent is to make this central data handling logic easily findable.

2.  **Base Entity Pattern:** The integration defines base classes for its entities:
    *   `OpenEPaperLinkBaseSensor` in `open_epaper_link/sensor.py`: This class serves as a base for `OpenEPaperLinkTagSensor` and `OpenEPaperLinkAPSensor`.
    *   `APConfigSelect` in `open_epaper_link/select.py`: This class serves as a base for `APTimeHourSelect` and is the foundation for other select entities configured in `SELECT_ENTITIES`.

The `open_epaper_link` integration currently does **NOT** follow this rule because:

*   The `Hub` class (acting as the coordinator) is located in `open_epaper_link/hub.py` instead of the recommended `open_epaper_link/coordinator.py`.
*   The base sensor class `OpenEPaperLinkBaseSensor` is located in `open_epaper_link/sensor.py` instead of `open_epaper_link/entity.py`.
*   The base select class `APConfigSelect` (and its helper `OptionMapping` class) is located in `open_epaper_link/select.py` instead of `open_epaper_link/entity.py`.

The integration is missing the `coordinator.py` and `entity.py` files.

## Suggestions

To make the `open_epaper_link` integration compliant with the `common-modules` rule, the following changes are recommended:

1.  **Refactor the Coordinator:**
    *   Rename the file `homeassistant/components/open_epaper_link/hub.py` to `homeassistant/components/open_epaper_link/coordinator.py`.
    *   The class name `Hub` can remain as is within the new `coordinator.py` file.
    *   Update all import statements that reference `Hub` from `.hub` to `.coordinator`. Affected files will likely include:
        *   `__init__.py`
        *   `button.py`
        *   `camera.py`
        *   `config_flow.py` (specifically `OptionsFlowHandler`)
        *   `select.py`
        *   `sensor.py`
        *   `switch.py`
        *   `text.py`
        *   `util.py` (if it uses the hub directly, though it seems to mostly take `hass` or `hub` as an argument)

    *Example import change in `__init__.py`:*
    ```diff
    # homeassistant/components/open_epaper_link/__init__.py
    ...
    from .const import DOMAIN
    -from .hub import Hub
    +from .coordinator import Hub
    from .services import async_setup_services, async_unload_services
    ...
    ```

2.  **Create `entity.py` and Relocate Base Entities:**
    *   Create a new file: `homeassistant/components/open_epaper_link/entity.py`.
    *   Move the `OpenEPaperLinkBaseSensor` class definition from `homeassistant/components/open_epaper_link/sensor.py` to the new `entity.py`.
        *   Update `homeassistant/components/open_epaper_link/sensor.py` to import `OpenEPaperLinkBaseSensor` from `.entity`.

        *Example structure for `entity.py` (initially with base sensor):*
        ```python
        # homeassistant/components/open_epaper_link/entity.py
        from homeassistant.components.sensor import SensorEntity
        # ... other necessary imports for OpenEPaperLinkBaseSensor

        class OpenEPaperLinkBaseSensor(SensorEntity):
            """Base class for all OpenEPaperLink sensors."""
            # ... (current implementation of OpenEPaperLinkBaseSensor) ...
        ```

        *Example import change in `sensor.py`:*
        ```diff
        # homeassistant/components/open_epaper_link/sensor.py
        # ...
        from homeassistant.helpers.typing import StateType

        import logging

        -from .const import DOMAIN
        -from .hub import Hub
        +# Assuming OpenEPaperLinkBaseSensor was defined in this file before
        +# Remove its definition from here
        +
        +from .const import DOMAIN
        +from .coordinator import Hub # If Hub was Hub, or its new name
        +from .entity import OpenEPaperLinkBaseSensor

        # ...

        -class OpenEPaperLinkBaseSensor(SensorEntity):
        -    """Base class for all OpenEPaperLink sensors."""
        -    # ...

        class OpenEPaperLinkTagSensor(OpenEPaperLinkBaseSensor):
            # ...
        ```

    *   Move the `APConfigSelect` class definition and the `OptionMapping` class definition from `homeassistant/components/open_epaper_link/select.py` to `entity.py`.
        *   Update `homeassistant/components/open_epaper_link/select.py` to import `APConfigSelect` and `OptionMapping` from `.entity`. The various `XXX_MAPPING` constants (e.g., `CHANNEL_MAPPING`) and the `SELECT_ENTITIES` list can remain in `select.py` as they define specific instances and configurations.

        *Example addition to `entity.py`:*
        ```python
        # homeassistant/components/open_epaper_link/entity.py
        # ... (OpenEPaperLinkBaseSensor and its imports) ...
        from homeassistant.components.select import SelectEntity

        class OptionMapping:
            """Base mapping class for handling value-to-option mapping."""
            # ... (current implementation of OptionMapping) ...

        class APConfigSelect(SelectEntity):
            """Base select entity for AP configuration."""
            # ... (current implementation of APConfigSelect, ensuring it imports OptionMapping locally if not globally in entity.py) ...
        ```

        *Example import change in `select.py`:*
        ```diff
        # homeassistant/components/open_epaper_link/select.py
        from __future__ import annotations

        -from homeassistant.components.select import SelectEntity
        from homeassistant.config_entries import ConfigEntry
        from homeassistant.core import HomeAssistant, callback
        from homeassistant.helpers.dispatcher import async_dispatcher_connect
        from homeassistant.helpers.entity import EntityCategory
        from homeassistant.helpers.entity_platform import AddEntitiesCallback

        from .const import DOMAIN
        -from .util import set_ap_config_item
        +from .coordinator import Hub # Assuming Hub is the class in coordinator.py
        +from .util import set_ap_config_item # Keep this if used by specific select entities
        +from .entity import APConfigSelect, OptionMapping # Import base classes

        import logging

        _LOGGER = logging.getLogger(__name__)

        -class OptionMapping:
        -    # ...

        # CHANNEL_MAPPING, BRIGHTNESS_MAPPING, etc. constants remain here

        -class APConfigSelect(SelectEntity):
        -    # ...

        class APTimeHourSelect(APConfigSelect): # This now inherits from the imported APConfigSelect
            # ...

        async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
            hub: Hub = hass.data[DOMAIN][entry.entry_id] # Ensure Hub type hint matches class from coordinator.py
            # ...
            # Instantiation of APConfigSelect and APTimeHourSelect will use the imported classes
        ```

3.  **Consider a Generic Base Entity:**
    Many entities across different platforms (`sensor.py`, `switch.py`, `camera.py`, `text.py`, `select.py`) share common patterns like:
    *   Storing a reference to the `Hub` (`self._hub`).
    *   Defining `device_info` based on the AP or a specific tag.
    *   Using `async_dispatcher_connect` to listen for updates from the `Hub`.
    *   Checking `self._hub.online` and tag presence for availability.

    Consider creating a generic base entity in `entity.py`, for example, `OpenEPaperLinkEntity`, from which other platform-specific base entities (like `OpenEPaperLinkBaseSensor`) or direct entities could inherit. This would further centralize common logic.

    *Example of a potential generic base entity:*
    ```python
    # homeassistant/components/open_epaper_link/entity.py
    from homeassistant.helpers.entity import Entity
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    from .const import DOMAIN # Assuming DOMAIN is needed
    # from .coordinator import Hub # Type hinting

    class OpenEPaperLinkEntity(Entity):
        """Base class for OpenEPaperLink entities."""

        def __init__(self, hub # : Hub
                    ) -> None:
            """Initialize the entity."""
            super().__init__()
            self._hub = hub
            # Common _attr_should_poll = False if updates are via dispatcher

        @property
        def available(self) -> bool:
            """Return if entity is available."""
            return self._hub.online # Basic availability, can be overridden

        # Potentially common async_added_to_hass for dispatcher connections
        # or methods to handle connection status.
    ```

By following these suggestions, the integration will align with the `common-modules` rule, enhancing its consistency with other Home Assistant integrations and making it easier for developers to understand and maintain the codebase.

_Created at 2025-05-14 20:34:17. Prompt tokens: 60403, Output tokens: 2510, Total tokens: 67448_
