# samsungtv: devices

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [devices](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/devices)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires integrations to create devices in the Home Assistant device registry to group related entities. This integration, `samsungtv`, correctly applies this rule.

The integration defines a base entity class `SamsungTVEntity` in `homeassistant/components/samsungtv/entity.py`. This class sets the `_attr_device_info` attribute, which is the standard way for entities to associate themselves with a device in the device registry.

Specifically, the `SamsungTVEntity` constructor populates `_attr_device_info` with the following information:

*   `manufacturer`: Set from `config_entry.data.get(CONF_MANUFACTURER)`, defaulting to "Samsung" (defined in `const.py`).
*   `model_id`: Set from `config_entry.data.get(CONF_MODEL)`, which is populated during the config flow (`config_flow.py`) based on discovered device info.
*   `identifiers`: Set using the domain (`DOMAIN`) and the `config_entry.unique_id` (or `config_entry.entry_id` as a fallback). The `config_flow.py` logic prioritizes using the UPnP UDN (`_udn`) as the unique ID when available, which serves as a stable device identifier.
*   `connections`: Set using the network MAC address (`dr.CONNECTION_NETWORK_MAC`, `self._mac`) if the MAC address is available from the configuration entry. The `config_flow.py` and `__init__.py` actively attempt to discover and store the MAC address.

By defining `_attr_device_info` in the base entity class with these details, all entities derived from `SamsungTVEntity` (like `MediaPlayerEntity` and `RemoteEntity` as seen in `media_player.py` and `remote.py`) are correctly grouped under a single device entry in the Home Assistant device registry. The information provided helps uniquely identify the Samsung TV device and provides useful metadata to the user.

The implementation aligns well with the example provided in the rule documentation, using the `DeviceInfo` object to link entities to a device and populate key identifying attributes.

## Suggestions

No suggestions needed.

_Created at 2025-05-25 11:30:54. Prompt tokens: 30116, Output tokens: 573, Total tokens: 31451_
