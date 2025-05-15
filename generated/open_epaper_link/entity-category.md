# open_epaper_link: entity-category

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://www.home-assistant.io/integrations/open_epaper_link/) |
| Rule   | [entity-category](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-category)                                                     |
| Status | **todo**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `entity-category` rule requires that entities are assigned an appropriate `EntityCategory` when their default category (which is `None`, implying a primary state/control entity) is inappropriate. This is important for correct classification and UI presentation, such as in auto-generated dashboards where `CONFIG` or `DIAGNOSTIC` entities might be hidden by default or grouped separately.

The rule applies to the `open_epaper_link` integration because it provides entities that serve configuration or diagnostic purposes, for which the default category `None` is not appropriate.

The integration generally follows this rule well for many of its entities:
*   **Sensors (`sensor.py`):** Many diagnostic sensors (e.g., `db_size`, `heap`, `wifi_rssi` for AP; `battery_voltage`, `lqi`, `rssi` for tags) are correctly assigned `EntityCategory.DIAGNOSTIC`. Sensors representing primary state (e.g., `temperature`, `battery_percentage`) correctly use the default category.
*   **Switches (`switch.py`):** All `APConfigSwitch` entities are correctly assigned `EntityCategory.CONFIG` as they control AP settings.
*   **Selects (`select.py`):** All `APConfigSelect` and `APTimeHourSelect` entities are correctly assigned `EntityCategory.CONFIG` as they configure AP settings.
*   **Buttons (`button.py`):** Most tag-specific buttons (e.g., `ClearPendingTagButton`, `RebootTagButton`) and the `RefreshTagTypesButton` are correctly assigned `EntityCategory.DIAGNOSTIC`.
*   **Text (`text.py`):** `APConfigText` entities are correctly assigned `EntityCategory.CONFIG`.

However, there are a couple of entities where the `EntityCategory` is missing or could be more appropriately set:

1.  **`button.RebootAPButton` (in `homeassistant/components/open_epaper_link/button.py`):**
    This button entity allows rebooting the Access Point. It currently does not have an `_attr_entity_category` set, meaning it defaults to `None`. A reboot action for a hub/device is typically considered a configuration or diagnostic control. Assigning `EntityCategory.CONFIG` would be appropriate, aligning with how similar control entities (like Home Assistant's own restart button) are categorized.

    ```python
    # homeassistant/components/open_epaper_link/button.py
    class RebootAPButton(ButtonEntity):
        """Button to reboot the Access Point."""
        def __init__(self, hass: HomeAssistant, hub) -> None:
            # ...
            # No _attr_entity_category is set here or in the class body
            # ...
    ```

2.  **`text.TagNameText` (in `homeassistant/components/open_epaper_link/text.py`):**
    This text entity allows users to set the alias (display name) for a tag. This is purely a configuration action for the tag device. It currently does not have an `_attr_entity_category` set, defaulting to `None`. It should be `EntityCategory.CONFIG`.

    ```python
    # homeassistant/components/open_epaper_link/text.py
    class TagNameText(TextEntity):
        """Text entity for tag name/alias."""
        def __init__(self, hub, tag_mac: str) -> None:
            # ...
            # No _attr_entity_category is set here or in the class body
            # ...
    ```

Because these entities have an inappropriate default category, the integration does not fully follow the `entity-category` rule.

## Suggestions

To make the `open_epaper_link` integration compliant with the `entity-category` rule, the following changes are recommended:

1.  **For `button.RebootAPButton`:**
    Assign `EntityCategory.CONFIG` to this button. This categorizes it as a configuration/control entity for the AP device.
    Modify `homeassistant/components/open_epaper_link/button.py` as follows:

    ```python
    # homeassistant/components/open_epaper_link/button.py
    from homeassistant.helpers.entity import EntityCategory # Ensure EntityCategory is imported

    # ...

    class RebootAPButton(ButtonEntity):
        """Button to reboot the Access Point."""
        _attr_entity_category = EntityCategory.CONFIG # Add this line

        def __init__(self, hass: HomeAssistant, hub) -> None:
            self.hass = hass
            self._hub = hub
            self._attr_has_entity_name = True
            self._attr_translation_key = "reboot_ap"
            self._attr_unique_id = "reboot_ap"
            self._attr_icon = "mdi:restart"
        # ... rest of the class
    ```
    *Why:* This change properly classifies the reboot button as a control related to the AP's configuration, which can influence how it's displayed or handled in auto-generated UIs.

2.  **For `text.TagNameText`:**
    Assign `EntityCategory.CONFIG` to this text entity. This correctly identifies it as an entity used for configuring a property (the alias) of a tag device.
    Modify `homeassistant/components/open_epaper_link/text.py` as follows:

    ```python
    # homeassistant/components/open_epaper_link/text.py
    from homeassistant.helpers.entity import EntityCategory # Ensure EntityCategory is imported

    # ...

    class TagNameText(TextEntity):
        """Text entity for tag name/alias."""
        _attr_entity_category = EntityCategory.CONFIG # Add this line

        def __init__(self, hub, tag_mac: str) -> None:
            self._hub = hub
            self._tag_mac = tag_mac
            self._attr_unique_id = f"{tag_mac}_alias"
            self._attr_has_entity_name = True
            self._attr_translation_key = "tag_alias"
            self._attr_native_min = 0
            self._attr_mode = TextMode.TEXT
            self._attr_icon = "mdi:rename"
        # ... rest of the class
    ```
    *Why:* This change ensures the tag alias text input is categorized as a configuration entity, which is its sole purpose.

By implementing these suggestions, the entities will be more appropriately classified, improving their handling and presentation within Home Assistant.

_Created at 2025-05-14 20:59:49. Prompt tokens: 60198, Output tokens: 1596, Total tokens: 64736_
