# stiebel_eltron: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [stiebel_eltron](https://www.home-assistant.io/integrations/stiebel_eltron/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **todo**                                                                 |
| Reason |                                                                          |

## Overview

The `appropriate-polling` rule requires that polling integrations set a specific, appropriate polling interval. This ensures that the integration polls the device or service at a frequency suitable for the data it provides, rather than relying on potentially unsuitable Home Assistant defaults.

This rule applies to the `stiebel_eltron` integration because:
1.  The `manifest.json` explicitly declares it as a polling integration:
    ```json
    "iot_class": "local_polling"
    ```
2.  The integration does not use a `DataUpdateCoordinator` for managing data updates.
3.  Instead, it relies on entity-based polling. The `StiebelEltron` entity in `climate.py` inherits from `ClimateEntity` (which inherits from `Entity`), where `should_poll` defaults to `True`. It also implements an `update()` method, which is called by Home Assistant to refresh entity state.

The `stiebel_eltron` integration currently does **NOT** follow this rule.
While it uses the entity-based polling mechanism, it fails to define a `SCAN_INTERVAL` constant in the `climate.py` platform module. The rule states:
> "When using the built-in entity update method, having set the `should_poll` entity attribute to `True`, the polling interval can be set by setting the `SCAN_INTERVAL` constant in the platform module."

By omitting `SCAN_INTERVAL`, the integration relies on a generic Home Assistant default polling interval, which may not be "appropriate" for Stiebel Eltron heat pumps. The integration developer is expected to determine and set a suitable interval.

**Code Reference (`homeassistant/components/stiebel_eltron/climate.py`):**
The file `climate.py` defines the `StiebelEltron` climate entity. At the module level, there is no `SCAN_INTERVAL` constant defined:

```python
# homeassistant/components/stiebel_eltron/climate.py

# Missing: from datetime import timedelta
# Missing: SCAN_INTERVAL = timedelta(seconds=YOUR_APPROPRIATE_INTERVAL)

import logging
# ... other imports

# ...

class StiebelEltron(ClimateEntity):
    """Representation of a STIEBEL ELTRON heat pump."""
    # _attr_should_poll is not set, so it defaults to True.
    # An update() method is defined.

    def update(self) -> None:
        """Update unit attributes."""
        self._client.update()
        # ...
```

Without `SCAN_INTERVAL`, the integration does not explicitly control its polling frequency as required by the rule.

## Suggestions

To make the `stiebel_eltron` integration compliant with the `appropriate-polling` rule, the following changes should be made in `homeassistant/components/stiebel_eltron/climate.py`:

1.  **Import `timedelta`:**
    Add the `timedelta` object from the `datetime` module at the beginning of the file.
    ```python
    from datetime import timedelta
    ```

2.  **Define `SCAN_INTERVAL`:**
    At the module level (i.e., outside any class definition, typically near the imports), define the `SCAN_INTERVAL` constant. The value should be a `timedelta` object representing an appropriate polling frequency for Stiebel Eltron heat pumps. For example, polling once per minute might be a reasonable starting point, but this should be evaluated based on the typical data update frequency of the device and the responsiveness desired by most users.

    ```python
    # homeassistant/components/stiebel_eltron/climate.py
    from datetime import timedelta
    import logging
    # ... other imports

    _LOGGER = logging.getLogger(__name__)

    # Define an appropriate scan interval.
    # For example, 60 seconds. This value should be chosen based on
    # how frequently the Stiebel Eltron device data realistically changes
    # and the desired responsiveness.
    SCAN_INTERVAL = timedelta(seconds=60)

    # ... rest of the file
    ```

**Why these changes satisfy the rule:**
By adding `SCAN_INTERVAL` to `climate.py`, the integration explicitly defines its polling interval. This fulfills the rule's requirement for the integration to "set an appropriate polling interval" itself, rather than relying on a generic system default. This allows for more responsible and efficient polling tailored to the specifics of Stiebel Eltron devices.

**Further Recommendation (Optional but good practice):**
While not strictly part of this rule, the current `update()` method in `StiebelEltron` class is synchronous:
```python
def update(self) -> None:
    """Update unit attributes."""
    self._client.update() # This is a blocking I/O call
    # ...
```
For better performance and adherence to Home Assistant's asynchronous architecture, this should be converted to an `async_update` method, and the blocking call `self._client.update()` should be run in the executor:
```python
async def async_update(self) -> None:
    """Update unit attributes."""
    await self.hass.async_add_executor_job(self._client.update)
    self._target_temperature = self._client.get_target_temp()
    # ... (update other attributes similarly)
```
This change is related to efficient data fetching and rule `parallel-updates`.

_Created at 2025-05-14 14:53:29. Prompt tokens: 6265, Output tokens: 1296, Total tokens: 11050_
