# jewish_calendar: stale-devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [stale-devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/stale-devices)                                                     |
| Status | **exempt**                                       |
| Reason | The integration creates a single 'service' device tied directly to its config entry, not representing an external device that can become stale. Its lifecycle is managed by Home Assistant core when the config entry is removed. |

## Overview

The `stale-devices` rule requires integrations to remove devices from Home Assistant when they are removed from an external hub or account, or to provide a mechanism for manual removal if automatic detection is not possible.

This rule does **not apply** to the `jewish_calendar` integration. Here's why:

1.  **Nature of the "Device":**
    The `jewish_calendar` integration creates a single "device" per configuration entry. As seen in `entity.py`:
    ```python
    self._attr_device_info = DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, config_entry.entry_id)},
    )
    ```
    This device is of `DeviceEntryType.SERVICE`, meaning it represents the configured instance of the integration service itself, rather than a physical or external virtual device. Its identifiers are directly linked to the `config_entry.entry_id`.

2.  **Single Configuration Entry:**
    The `manifest.json` specifies `"single_config_entry": true`. This means the integration supports only one configuration entry at a time. Consequently, there is only one such "service" device associated with the `jewish_calendar` integration.

3.  **No External Hub or Account:**
    The `jewish_calendar` integration is `iot_class: "calculated"`. It does not communicate with an external hub, cloud service, or account from which devices could be added or removed. The data it provides is calculated based on its configuration (location, time settings, etc.). Therefore, there is no external source where a device could become "stale" or be "removed."

4.  **Lifecycle Management by Home Assistant Core:**
    The "device" created by `jewish_calendar` is intrinsically tied to its config entry. If the user removes the `jewish_calendar` config entry from Home Assistant, Home Assistant core automatically handles the removal of the associated device and all its entities. There is no scenario where this "service" device would become stale independently of its config entry while the config entry itself remains active.

5.  **Rule's Intent:**
    The `stale-devices` rule is primarily aimed at integrations that manage multiple devices (often from a coordinator or hub) where individual devices can be removed or become unavailable at the source. `jewish_calendar` does not fit this model. It does not poll for a list of devices, nor does it have devices that can be individually "lost" or "removed" from an external system.

Given these points, the concept of a "stale device" as described by the rule does not apply to the `jewish_calendar` integration. The integration does not need to implement logic to detect or allow manual removal of stale devices because its single, service-type device's lifecycle is inherently tied to its configuration entry, which is managed by Home Assistant core.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:33:07. Prompt tokens: 13876, Output tokens: 789, Total tokens: 17783_
