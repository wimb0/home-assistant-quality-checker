# saj_modbus: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **done**                                                                 |

## Overview

The `appropriate-polling` rule applies to this integration, as it is a local polling integration, confirmed by `"iot_class": "local_polling"` in its `manifest.json` file. The integration polls a SAJ R5 Solar Inverter via the Modbus protocol to retrieve data.

The integration correctly follows this rule by implementing a `DataUpdateCoordinator` with a configurable polling interval and a sensible default.

1.  **Use of `DataUpdateCoordinator`**: The integration uses a `DataUpdateCoordinator` subclass named `SAJModbusHub` in `hub.py` to manage data fetching.

2.  **Setting `update_interval`**: The `update_interval` for the coordinator is correctly set during its initialization. The interval is passed as an argument and converted to a `timedelta` object.

    ```python
    # homeassistant/components/saj_modbus/hub.py L:37-43
    def __init__(
        self,
        # ...
        scan_interval: Number,
    ):
        """Initialize the Modbus hub."""
        super().__init__(
            # ...
            update_interval=timedelta(seconds=scan_interval),
        )
    ```

3.  **Default Polling Interval**: A default polling interval is defined in `const.py` and used throughout the integration.

    ```python
    # homeassistant/components/saj_modbus/const.py L:18
    DEFAULT_SCAN_INTERVAL = 60
    ```
    A default of 60 seconds is a reasonable and appropriate interval for a local solar inverter, as it provides timely updates for energy monitoring without excessively loading the device.

4.  **User-Configurable Interval**: The integration allows users to set a custom polling interval during the initial setup and to modify it later via an options flow. The code in `__init__.py` prioritizes the user-configured option, falling back to the default.

    ```python
    # homeassistant/components/saj_modbus/__init__.py L:46
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    ```
    The options flow in `config_flow.py` provides the UI for this customization.

The implementation aligns perfectly with the best practices outlined in the rule documentation.

## Suggestions

No suggestions needed.

---

_Created at 2025-06-11 21:30:24. Prompt tokens: 16823, Output tokens: 634, Total tokens: 19497._

_AI can be wrong. Always verify the report and the code against the rule._
