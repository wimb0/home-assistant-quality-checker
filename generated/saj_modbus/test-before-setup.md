# saj_modbus: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [saj_modbus](https://www.home-assistant.io/integrations/saj_modbus/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                                                 |

## Overview

The `test-before-setup` rule applies to this integration as it connects to a local network device (a Modbus inverter), and this connection can fail due to network issues, an incorrect address, or the device being offline. The integration should test this connection during setup and raise an appropriate exception to inform the user and allow Home Assistant to retry.

The integration attempts to follow this rule by using a `DataUpdateCoordinator` and calling `await hub.async_config_entry_first_refresh()` in `__init__.py`. This is the recommended pattern, as it triggers an immediate data fetch, and any exceptions raised during this fetch will be handled by Home Assistant to signal a setup failure.

However, the implementation within the `SAJModbusHub` class in `hub.py` prevents this mechanism from working correctly.

1.  In `hub.py`, the `_async_update_data` method wraps the Modbus communication calls in a `try...except` block. When a `ConnectionException` or similar error occurs, it catches the exception, logs an error, and then proceeds to return a dictionary with default/fallback values. It does not re-raise an exception.
2.  Similarly, the `read_modbus_inverter_data` and `read_modbus_r5_realtime_data` methods check for Modbus errors with `inverter_data.isError()` but simply return an empty dictionary `{}` instead of raising an exception.

Because exceptions are caught and handled internally without being propagated, `async_config_entry_first_refresh()` always completes successfully. This leads to the integration finishing its setup even when the inverter is unreachable. The user is not notified of the problem, and the entities are created in an unavailable or incorrect state, which is a poor user experience.

**Code Reference (`hub.py`):**
```python
# homeassistant/components/saj_modbus/hub.py

    async def _async_update_data(self) -> dict:
        realtime_data = {}
        try:
            # ... modbus reading ...
        except (BrokenPipeError, ConnectionResetError, ConnectionException) as conerr:
            _LOGGER.error("Reading realtime data failed! Inverter is unreachable.")
            _LOGGER.debug("Connection error: %s", conerr)
            # This block prevents setup failure by returning default data
            # instead of raising an exception.
            realtime_data["mpvmode"] = 0
            realtime_data["mpvstatus"] = DEVICE_STATUSSES[0]
            realtime_data["power"] = 0

        self.close()
        return {**self.inverter_data, **realtime_data}

    def read_modbus_inverter_data(self) -> dict:
        """Read data about inverter."""
        inverter_data = self._read_holding_registers(unit=1, address=0x8F00, count=29)

        if inverter_data.isError():
            return {} # Should raise an exception here

        # ...
```

## Suggestions

To comply with the rule, the integration must allow connection exceptions to propagate during the initial setup. This can be achieved by raising an `UpdateFailed` exception from the coordinator's update method when communication fails.

1.  **Modify `read_modbus_*` methods:** In `hub.py`, change `read_modbus_inverter_data` and `read_modbus_r5_realtime_data` to raise a `ModbusException` (or a custom exception) when `isError()` is true, instead of returning an empty dictionary.

2.  **Modify `_async_update_data`:** In `hub.py`, refactor the `try...except` block inside `_async_update_data`. It should catch all relevant communication exceptions (including `ModbusException` from the change above) and raise `homeassistant.helpers.update_coordinator.UpdateFailed`.

This change will cause `hub.async_config_entry_first_refresh()` to raise a `ConfigEntryNotReady` exception, correctly signaling to Home Assistant that the setup failed and should be retried automatically.

**Example Implementation (`hub.py`):**
```python
# homeassistant/components/saj_modbus/hub.py

# Add required imports
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.exceptions import ConnectionException, ModbusException
# ...

class SAJModbusHub(DataUpdateCoordinator[dict]):
    # ...

    async def _async_update_data(self) -> dict:
        """Fetch data from the inverter."""
        try:
            # The close() call should be inside a try...finally block if it's
            # intended to run after each attempt, or before the return.
            # Here we assume it's part of the successful path.
            
            """Inverter info is only fetched once"""
            if not self.inverter_data:
                self.inverter_data = await self.hass.async_add_executor_job(
                    self.read_modbus_inverter_data
                )
            """Read realtime data"""
            realtime_data = await self.hass.async_add_executor_job(
                self.read_modbus_r5_realtime_data
            )

        except (BrokenPipeError, ConnectionResetError, ConnectionException, ModbusException) as ex:
            # Re-raise as UpdateFailed so the coordinator can handle it.
            # During first refresh, this will become ConfigEntryNotReady.
            raise UpdateFailed(f"Error communicating with inverter: {ex}") from ex
        
        # This should only be called on a successful update.
        self.close()
        return {**self.inverter_data, **realtime_data}

    def read_modbus_inverter_data(self) -> dict:
        """Read data about inverter."""
        inverter_data = self._read_holding_registers(unit=1, address=0x8F00, count=29)

        if inverter_data.isError():
            # Raise an exception instead of returning empty data
            raise ModbusException("Failed to read inverter data, response is error.")
        
        # ... (rest of the function) ...
        return data

    def read_modbus_r5_realtime_data(self) -> dict:
        """Read realtime data from inverter."""
        realtime_data = self._read_holding_registers(unit=1, address=0x100, count=60)

        if realtime_data.isError():
            # Raise an exception instead of returning empty data
            raise ModbusException("Failed to read realtime data, response is error.")

        # ... (rest of the function) ...
        return data

    # ...
```

---

_Created at 2025-06-11 21:36:06. Prompt tokens: 16722, Output tokens: 1654, Total tokens: 21435._

_AI can be wrong. Always verify the report and the code against the rule._
