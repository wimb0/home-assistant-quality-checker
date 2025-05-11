# wled: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default)                                                     |
| Status | **todo**                                                                 |

## Overview

The `entity-disabled-by-default` rule states that integrations should disable less popular or noisy entities by default to conserve resources. Users can enable them if they have a specific use case. This rule applies to the `wled` integration as it provides sensor entities, some of which are diagnostic in nature.

The `wled` integration partially follows this rule. In `sensor.py`, several diagnostic sensor entities are correctly disabled by default by setting `entity_registry_enabled_default=False` in their `WLEDSensorEntityDescription`. These include:
*   `uptime`
*   `free_heap`
*   `wifi_signal`
*   `wifi_rssi`
*   `wifi_channel`
*   `wifi_bssid`

However, the following sensor entities, also categorized as `EntityCategory.DIAGNOSTIC`, are currently enabled by default (they lack the `entity_registry_enabled_default=False` setting):

*   **`estimated_current`**: This sensor (`sensor.py`) shows the estimated current draw. It is diagnostic and can be "noisy" as its state may change frequently with light brightness or effect changes. This makes it a strong candidate for being disabled by default.
*   **`info_leds_count`**: This sensor (`sensor.py`) displays the number of LEDs. It's diagnostic and, while not noisy (as it's typically a static value post-configuration), it can be considered "less popular" for daily use after initial setup.
*   **`info_leds_max_power`**: Similar to `info_leds_count`, this sensor (`sensor.py`) shows the maximum configured power. It's diagnostic, static, and likely "less popular."
*   **`ip`**: This sensor (`sensor.py`) displays the device's IP address. It is diagnostic and, while useful for troubleshooting, is "less popular" for typical automations or frequent dashboard display.

Other entity types provided by the WLED integration (light, switch, number, select, button, update) are generally core to the device's functionality or are configuration/control entities. These are appropriately enabled by default and are not the primary focus of this rule, which targets entities that might unnecessarily consume resources through state tracking if not actively used.

## Suggestions

To fully comply with the `entity-disabled-by-default` rule, the following sensor entities should be disabled by default. This can be achieved by adding `entity_registry_enabled_default=False` to their respective `WLEDSensorEntityDescription` in `sensor.py`.

1.  **`estimated_current`**:
    This entity is diagnostic and can be noisy.
    Modify its description in the `SENSORS` tuple in `sensor.py`:
    ```python
    WLEDSensorEntityDescription(
        key="estimated_current",
        translation_key="estimated_current",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Add this line
        value_fn=lambda device: device.info.leds.power,
        exists_fn=lambda device: bool(device.info.leds.max_power),
    ),
    ```

2.  **`info_leds_count`**:
    This entity is diagnostic and less popular for frequent monitoring.
    Modify its description in `sensor.py`:
    ```python
    WLEDSensorEntityDescription(
        key="info_leds_count",
        translation_key="info_leds_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Add this line
        value_fn=lambda device: device.info.leds.count,
    ),
    ```

3.  **`info_leds_max_power`**:
    This entity is diagnostic and less popular.
    Modify its description in `sensor.py`:
    ```python
    WLEDSensorEntityDescription(
        key="info_leds_max_power",
        translation_key="info_leds_max_power",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=False,  # Add this line
        value_fn=lambda device: device.info.leds.max_power,
        exists_fn=lambda device: bool(device.info.leds.max_power),
    ),
    ```

4.  **`ip`**:
    This entity is diagnostic and generally less popular for daily use.
    Modify its description in `sensor.py`:
    ```python
    WLEDSensorEntityDescription(
        key="ip",
        translation_key="ip",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Add this line
        value_fn=lambda device: device.info.ip,
    ),
    ```

By making these changes, the integration will default to a more resource-conscious state, allowing users to explicitly enable these diagnostic entities if they find them useful, aligning with the intent of the `entity-disabled-by-default` rule.

_Created at 2025-05-10 23:01:45. Prompt tokens: 21489, Output tokens: 1353, Total tokens: 26382_
