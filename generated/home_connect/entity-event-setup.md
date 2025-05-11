# home_connect: entity-event-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [entity-event-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-event-setup)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `entity-event-setup` rule requires that entities subscribing to events (e.g., from an integration library or, in this case, a coordinator) do so in `async_added_to_hass` and unsubscribe in `async_will_remove_from_hass`. The simplified `async_on_remove` pattern is preferred for managing these subscriptions.

The `home_connect` integration uses a `DataUpdateCoordinator`. Entities subscribe to this coordinator for updates. The `CoordinatorEntity` base class, from which all `home_connect` entities inherit (via `HomeConnectEntity`), correctly handles the primary listener registration and unregistration using `self.async_on_remove()` within its `async_added_to_hass` method. This ensures that the basic listener for coordinator updates is managed according to the rule.

Several entity classes in `home_connect` also subscribe to *additional* specific updates from the coordinator. These subscriptions are correctly established within their `async_added_to_hass` methods using the `self.async_on_remove()` pattern, which is compliant with the rule:
-   `HomeConnectProgramSensor` in `sensor.py`
-   `HomeConnectLight` in `light.py`
-   `HomeConnectProgramSelectEntity` in `select.py`

However, two entity classes override the `async_will_remove_from_hass` method but fail to call `await super().async_will_remove_from_hass()`:
1.  **`HomeConnectTimeEntity`** in `time.py`:
    ```python
    # time.py
    class HomeConnectTimeEntity(HomeConnectEntity, TimeEntity):
        # ...
        async def async_will_remove_from_hass(self) -> None:
            """Call when entity will be removed from hass."""
            if self.bsh_key is SettingKey.BSH_COMMON_ALARM_CLOCK:
                async_delete_issue(
                    self.hass,
                    DOMAIN,
                    f"deprecated_time_alarm_clock_in_automations_scripts_{self.entity_id}",
                )
                async_delete_issue(
                    self.hass, DOMAIN, f"deprecated_time_alarm_clock_{self.entity_id}"
                )
            # MISSING: await super().async_will_remove_from_hass()
    ```

2.  **`HomeConnectProgramSwitch`** in `switch.py`:
    ```python
    # switch.py
    class HomeConnectProgramSwitch(HomeConnectEntity, SwitchEntity):
        # ...
        async def async_will_remove_from_hass(self) -> None:
            """Call when entity will be removed from hass."""
            async_delete_issue(
                self.hass,
                DOMAIN,
                f"deprecated_program_switch_in_automations_scripts_{self.entity_id}",
            )
            async_delete_issue(
                self.hass, DOMAIN, f"deprecated_program_switch_{self.entity_id}"
            )
            # MISSING: await super().async_will_remove_from_hass()
    ```

While Home Assistant's entity platform helpers ensure that callbacks registered with `async_on_remove` (like the one used by `CoordinatorEntity` to remove its listener) are typically called even if `super().async_will_remove_from_hass()` is omitted, it is a deviation from best practices and the explicit example provided in the rule documentation. The rule's example for `async_will_remove_from_hass` clearly includes `await super().async_will_remove_from_hass()`. Omitting this call can break the cleanup chain if base classes have essential logic in their `async_will_remove_from_hass` methods that isn't managed by `async_on_remove`, or if the order of cleanup operations is critical.

Therefore, the integration is marked as "todo" because these specific entities do not fully adhere to the pattern shown in the rule's example implementation regarding overridden lifecycle methods.

## Suggestions

To make the `home_connect` integration fully compliant with the `entity-event-setup` rule, ensure that all overridden `async_will_remove_from_hass` methods call their superclass's implementation.

1.  **Modify `HomeConnectTimeEntity` in `time.py`:**
    Add `await super().async_will_remove_from_hass()` at the end of the `async_will_remove_from_hass` method.

    ```python
    # time.py
    class HomeConnectTimeEntity(HomeConnectEntity, TimeEntity):
        # ...
        async def async_will_remove_from_hass(self) -> None:
            """Call when entity will be removed from hass."""
            if self.bsh_key is SettingKey.BSH_COMMON_ALARM_CLOCK:
                async_delete_issue(
                    self.hass,
                    DOMAIN,
                    f"deprecated_time_alarm_clock_in_automations_scripts_{self.entity_id}",
                )
                async_delete_issue(
                    self.hass, DOMAIN, f"deprecated_time_alarm_clock_{self.entity_id}"
                )
            await super().async_will_remove_from_hass() # ADD THIS LINE
    ```

2.  **Modify `HomeConnectProgramSwitch` in `switch.py`:**
    Add `await super().async_will_remove_from_hass()` at the end of the `async_will_remove_from_hass` method.

    ```python
    # switch.py
    class HomeConnectProgramSwitch(HomeConnectEntity, SwitchEntity):
        # ...
        async def async_will_remove_from_hass(self) -> None:
            """Call when entity will be removed from hass."""
            async_delete_issue(
                self.hass,
                DOMAIN,
                f"deprecated_program_switch_in_automations_scripts_{self.entity_id}",
            )
            async_delete_issue(
                self.hass, DOMAIN, f"deprecated_program_switch_{self.entity_id}"
            )
            await super().async_will_remove_from_hass() # ADD THIS LINE
    ```

**Why these changes satisfy the rule:**
By calling `await super().async_will_remove_from_hass()`, these entities ensure that any cleanup logic implemented in their base classes (including `HomeConnectEntity` and `CoordinatorEntity`) is properly executed. This adheres to standard object-oriented practices for overridden methods and aligns with the example implementation provided in the rule documentation, ensuring robust resource management and preventing potential issues related to incomplete cleanup.

_Created at 2025-05-10 20:23:08. Prompt tokens: 139844, Output tokens: 1612, Total tokens: 148886_
