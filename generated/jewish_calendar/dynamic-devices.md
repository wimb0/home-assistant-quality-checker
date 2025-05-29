# jewish_calendar: dynamic-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [dynamic-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices)                                                     |
| Status | **exempt**                                       |
| Reason | The integration manages a single "device" per configuration entry (and is `single_config_entry: true`), providing a statically defined set of entities. It does not discover or manage a dynamic list of multiple, independent devices that can be added after the initial setup. |

## Overview

The `dynamic-devices` rule mandates that integrations should automatically create entities for new devices that are connected or become available *after* the integration has been initially set up. This rule is primarily aimed at integrations that manage multiple, potentially changing, devices (e.g., hubs controlling various child devices, network scanners discovering new hosts).

The `jewish_calendar` integration is **exempt** from this rule because it does not operate in a way where "new devices" can dynamically appear. Here's why:

1.  **Single Configuration, Single "Device"**:
    *   The `manifest.json` specifies `"single_config_entry": true`. This means users can only configure one instance of the Jewish Calendar integration.
    *   This single configuration results in a single logical "device" in Home Assistant, which groups all the related sensor and binary_sensor entities. This "device" is identified by `config_entry.entry_id` as seen in `entity.py`:
        ```python
        # homeassistant/components/jewish_calendar/entity.py
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, config_entry.entry_id)},
        )
        ```
    There is no mechanism or expectation for additional, independent "Jewish Calendar devices" to be discovered or added dynamically after the initial setup of this single configuration.

2.  **Statically Defined Entities**:
    *   The entities provided by `jewish_calendar` (various zmanim times, holiday information, etc.) are predefined. The `sensor.py` file lists `INFO_SENSORS` and `TIME_SENSORS`, and `binary_sensor.py` lists `BINARY_SENSORS`.
        ```python
        # homeassistant/components/jewish_calendar/sensor.py
        async def async_setup_entry(
            hass: HomeAssistant,
            config_entry: JewishCalendarConfigEntry,
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            """Set up the Jewish calendar sensors ."""
            sensors: list[JewishCalendarBaseSensor] = [
                JewishCalendarSensor(config_entry, description) for description in INFO_SENSORS
            ]
            sensors.extend(
                JewishCalendarTimeSensor(config_entry, description)
                for description in TIME_SENSORS
            )
            async_add_entities(sensors)
        ```
    *   These entities are created once during `async_setup_entry`. Their existence and type are determined by the integration's code, not by dynamic discovery of external devices.

3.  **No Dynamic Device Discovery Mechanism**:
    *   The rule's example implementation shows a coordinator fetching a list of devices and checking for new ones (`new_devices = current_devices - known_devices`).
    *   `jewish_calendar` does not have such a mechanism. Its data (`JewishCalendarData`) is derived from its configuration (location, diaspora status, etc.) and calculations based on the current time. It doesn't poll an external service or hardware for a list of devices that might change.
    *   Updates to the configuration (e.g., changing location via options flow) trigger a reload of the existing config entry (`await hass.config_entries.async_reload(config_entry.entry_id)` in `__init__.py`), which updates the existing entities. This is not the same as adding *new, distinct* devices.

In summary, the `jewish_calendar` integration is designed to provide a set of information based on a single, user-defined configuration. The concept of "new devices" appearing dynamically, which this rule addresses, does not apply to its architecture.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:23:19. Prompt tokens: 13607, Output tokens: 995, Total tokens: 16126_
