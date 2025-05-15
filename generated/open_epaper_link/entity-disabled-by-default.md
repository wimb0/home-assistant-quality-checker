# open_epaper_link: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default)                                                     |
| Status | **todo**                                                                 |

## Overview

The `entity-disabled-by-default` rule applies to the `open_epaper_link` integration. This rule mandates that entities considered less popular or noisy (i.e., changing state frequently) should be disabled by default. This practice helps conserve system resources by not tracking the history of these entities unless a user explicitly enables them.

The `open_epaper_link` integration creates numerous sensor entities for both the Access Point (AP) and individual tags. Many of these sensors are diagnostic in nature, provide highly technical information, or update frequently.

Currently, the integration does **not** fully follow this rule.
Most sensor entities are enabled by default. This is primarily because the `OpenEPaperLinkSensorEntityDescription` dataclass in `sensor.py` defaults `entity_registry_enabled_default` to `True`:

```python
# homeassistant/components/open_epaper_link/sensor.py
@dataclass(kw_only=True, frozen=True)
class OpenEPaperLinkSensorEntityDescription(SensorEntityDescription):
    # ...
    entity_registry_enabled_default: bool = True # Default is True
    # ...
```

Only one sensor, `sys_time` for the AP, correctly sets `entity_registry_enabled_default=False`:
```python
# homeassistant/components/open_epaper_link/sensor.py
    OpenEPaperLinkSensorEntityDescription(
        key="sys_time",
        name="System Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False, # Correctly disabled
        value_fn=lambda data: datetime.fromtimestamp(data.get("sys_time", 0), tz=timezone.utc),
        icon="mdi:clock-outline",
    ),
```

However, many other diagnostic and/or noisy sensors remain enabled by default.

**AP Sensors enabled by default that should be considered for disabling:**
Many are marked with `entity_category=EntityCategory.DIAGNOSTIC`.
*   `db_size`: Diagnostic, less popular.
*   `little_fs_free`: Diagnostic, less popular.
*   `wifi_rssi`: Diagnostic, can be noisy.
*   `heap`: Diagnostic, can be noisy.
*   `uptime`: Diagnostic, very noisy (updates every second).
*   `ps_ram_free`: Diagnostic, can be noisy.

**Tag Sensors enabled by default that should be considered for disabling:**
Many are marked with `entity_category=EntityCategory.DIAGNOSTIC`.
*   `battery_voltage`: Diagnostic (raw value, `battery_percentage` is more user-friendly).
*   `last_seen`: Timestamp, noisy.
*   `next_update`: Timestamp, noisy.
*   `next_checkin`: Timestamp, noisy.
*   `lqi`: Diagnostic, can be noisy.
*   `rssi`: Diagnostic, can be noisy.
*   `pending_updates`: Diagnostic, less popular.
*   `wakeup_reason`: Diagnostic, less popular.
*   `capabilities`: Diagnostic, technical.
*   `update_count`: Diagnostic, can be noisy.
*   `width`: Diagnostic, static but less popular for general users.
*   `height`: Diagnostic, static but less popular for general users.
*   `runtime`: Diagnostic, noisy.
*   `boot_count`: Diagnostic, less popular.
*   `checkin_count`: Diagnostic, can be noisy.
*   `block_requests`: Diagnostic, can be noisy.

Entities from other platforms like `button`, `camera`, `select`, `switch`, and `text` are primarily control or configuration entities. They either don't have a frequently changing state that is historically tracked in the same way as sensors, or they represent essential controls. The rule's reasoning about resource cost from state history tracking applies most directly to sensor entities.

## Suggestions

To comply with the `entity-disabled-by-default` rule, the `open_epaper_link` integration should disable diagnostic, less popular, and noisy sensor entities by default. This involves modifying the `OpenEPaperLinkSensorEntityDescription` instances in `sensor.py`.

For each of the identified sensor entity descriptions in `AP_SENSOR_TYPES` and `TAG_SENSOR_TYPES` below, add the attribute `entity_registry_enabled_default=False`.

**Example modification:**
For the `db_size` AP sensor:
```python
# homeassistant/components/open_epaper_link/sensor.py
    OpenEPaperLinkSensorEntityDescription(
        key="db_size",
        name="Database Size",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.KIBIBYTES,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False, # Add this line
        value_fn=lambda data: int(data.get("db_size", 0)),
        icon="mdi:database-settings",
    ),
```

**1. Modify AP Sensors in `AP_SENSOR_TYPES` (`sensor.py`):**
   Set `entity_registry_enabled_default=False` for the following:
    *   `db_size`
    *   `little_fs_free`
    *   `wifi_rssi`
    *   `heap`
    *   `uptime`
    *   `ps_ram_free`

**2. Modify Tag Sensors in `TAG_SENSOR_TYPES` (`sensor.py`):**
   Set `entity_registry_enabled_default=False` for the following:
    *   `battery_voltage`
    *   `last_seen`
    *   `next_update`
    *   `next_checkin`
    *   `lqi`
    *   `rssi`
    *   `pending_updates`
    *   `wakeup_reason`
    *   `capabilities`
    *   `update_count`
    *   `width`
    *   `height`
    *   `runtime`
    *   `boot_count`
    *   `checkin_count`
    *   `block_requests`

**Reasoning for these changes:**
By disabling these entities by default, the integration will:
*   Reduce the default number of entities created, leading to a cleaner user experience.
*   Save system resources by not recording the state history for these often noisy or less critical diagnostic entities unless the user specifically needs them.
*   Align with Home Assistant best practices for integration quality.

Users who require these specific diagnostic or detailed sensors can easily enable them through the Home Assistant UI.

_Created at 2025-05-14 21:01:54. Prompt tokens: 60536, Output tokens: 1680, Total tokens: 67137_
