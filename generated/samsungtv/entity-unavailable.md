```markdown
# samsungtv: entity-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [entity-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-unavailable)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `entity-unavailable` rule requires that entities should be marked as unavailable if the integration cannot successfully fetch data from the device or service they represent. This integration interacts with Samsung TVs, which can become unavailable due to network issues, being powered off, or authentication failures. Therefore, this rule applies to the `samsungtv` integration.

The `samsungtv` integration uses a `DataUpdateCoordinator` (`SamsungTVDataUpdateCoordinator`) and `CoordinatorEntity` (`SamsungTVEntity`). While the coordinator's `_async_update_data` method does not strictly follow the example of raising `UpdateFailed` for connectivity issues (it checks `self.bridge.async_is_on()` and updates `self.is_on`), the base entity's `available` property correctly incorporates the connectivity status reported by the bridge and coordinator to mark the entity as unavailable when communication fails.

The `SamsungTVEntity.available` property, defined in `homeassistant/components/samsungtv/entity.py`, determines the availability:

```python
    @property
    def available(self) -> bool:
        """Return the availability of the device."""
        if not super().available or self._bridge.auth_failed:
            return False
        return (
            self.coordinator.is_on
            or bool(self._turn_on_action)
            or self._mac is not None
            or self._bridge.power_off_in_progress
        )
```

This property evaluates to `False` (marking the entity unavailable) under the following conditions:

1.  `super().available` is `False`: This is the standard `DataUpdateCoordinator` behavior, which will be `False` if the `coordinator._async_update_data` method raised an exception (though `_async_update_data` primarily updates `self.is_on` rather than raising exceptions for connectivity).
2.  `self._bridge.auth_failed` is `True`: This flag is set by the bridge if authentication fails during communication attempts (e.g., in `SamsungTVWSBridge._async_get_remote_under_lock`).
3.  If the conditions above are met, the entity is unavailable. Otherwise, it is available *only if* the final expression `(self.coordinator.is_on or bool(self._turn_on_action) or self._mac is not None or self._bridge.power_off_in_progress)` is `True`.

The crucial part for connectivity failure is `self.coordinator.is_on`. The `SamsungTVDataUpdateCoordinator._async_update_data` method calls `await self.bridge.async_is_on()` and sets `self.is_on` accordingly. The `SamsungTVBridge.async_is_on()` implementations (in `SamsungTVWSBridge` and `SamsungTVLegacyBridge`) attempt communication and return `False` if the connection fails due to various network or communication errors (caught within the bridge methods like `_async_get_remote_under_lock` or `_is_on`).

Therefore, if the bridge fails to communicate with the TV, `self.coordinator.is_on` becomes `False`. Coupled with the conditions in the `available` property (which correctly handles scenarios like the TV being actively turned on or off), the entity is appropriately marked as unavailable.

Although the implementation deviates slightly from the coordinator example's pattern of raising `UpdateFailed` for connectivity issues, the result is the same: the entity's `available` state accurately reflects the ability to communicate with the device, adhering to the rule's requirement.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:30:06. Prompt tokens: 30376, Output tokens: 899, Total tokens: 34054_
