# jewish_calendar: entity-disabled-by-default

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [entity-disabled-by-default](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `entity-disabled-by-default` rule requires integrations to disable less popular or noisy entities by default. This is achieved by setting `_attr_entity_registry_enabled_default = False` (or `entity_registry_enabled_default=False` in an `EntityDescription`) for such entities.

This rule applies to the `jewish_calendar` integration as it provides multiple sensor and binary_sensor entities.

The integration **follows** this rule. It defines a set of core entities that are enabled by default and a larger set of more specialized or supplementary entities that are disabled by default. This allows users to get essential Jewish calendar information without being overwhelmed by numerous entities, while still providing the option to enable more detailed sensors as needed.

**Code Analysis:**

The integration defines its entities primarily in `sensor.py` and `binary_sensor.py` using `EntityDescription` dataclasses.

**1. Sensor Entities (`sensor.py`):**

*   **Enabled by default** (i.e., `entity_registry_enabled_default` is not set to `False`):
    *   `date` (Hebrew date): Core information.
    *   `weekly_portion`: Core information.
    *   `holiday`: Core information.
    *   `netz_hachama` (Halachic sunrise): A fundamental Zman (halachic time).
    *   `shkia` (Sunset): A fundamental Zman.
    *   `upcoming_candle_lighting`: General candle lighting time for Shabbat/Yom Tov.
    *   `upcoming_havdalah`: General Havdalah time for Shabbat/Yom Tov.

*   **Disabled by default** (explicitly set `entity_registry_enabled_default=False`):
    *   `omer_count`: Relevant only for a specific period of the year.
    *   `daf_yomi`: Specific Talmud study cycle, not universally followed.
    *   Many specific Zmanim (halachic times) like `alot_hashachar`, `talit_and_tefillin`, `sof_zman_shema_gra`/`mga`, `sof_zman_tfilla_gra`/`mga`, `chatzot_hayom`, `mincha_gedola`/`ketana`, `plag_hamincha`, `tset_hakohavim_tsom`/`shabbat`. These are often more specialized than basic sunrise/sunset.
    *   `upcoming_shabbat_candle_lighting`: Specific to Shabbat, potentially redundant if the general `upcoming_candle_lighting` (which is enabled) covers Shabbat.
    *   `upcoming_shabbat_havdalah`: Specific to Shabbat, potentially redundant if the general `upcoming_havdalah` (which is enabled) covers Shabbat.

    Example from `sensor.py`:
    ```python
    INFO_SENSORS: tuple[JewishCalendarSensorDescription, ...] = (
        # ...
        JewishCalendarSensorDescription(
            key="omer_count",
            translation_key="omer_count",
            entity_registry_enabled_default=False, # Disabled by default
            # ...
        ),
        JewishCalendarSensorDescription(
            key="daf_yomi",
            translation_key="daf_yomi",
            entity_registry_enabled_default=False, # Disabled by default
            # ...
        ),
    )

    TIME_SENSORS: tuple[JewishCalendarTimestampSensorDescription, ...] = (
        JewishCalendarTimestampSensorDescription(
            key="alot_hashachar",
            translation_key="alot_hashachar",
            entity_registry_enabled_default=False, # Disabled by default
        ),
        # ... many other time sensors also disabled by default
    )
    ```

**2. Binary Sensor Entities (`binary_sensor.py`):**

*   **Enabled by default**:
    *   `issur_melacha_in_effect`: Indicates if work restrictions (Shabbat/Holiday) are currently active. This is a key status.

*   **Disabled by default** (explicitly set `entity_registry_enabled_default=False`):
    *   `erev_shabbat_hag`: Indicates if it's the eve of Shabbat/Holiday. Useful, but supplementary to the "in effect" sensor.
    *   `motzei_shabbat_hag`: Indicates if it's the night after Shabbat/Holiday. Useful, but supplementary.

    Example from `binary_sensor.py`:
    ```python
    BINARY_SENSORS: tuple[JewishCalendarBinarySensorEntityDescription, ...] = (
        JewishCalendarBinarySensorEntityDescription(
            key="issur_melacha_in_effect",
            translation_key="issur_melacha_in_effect",
            # entity_registry_enabled_default is not False, so it's enabled
            is_on=lambda state, now: bool(state.issur_melacha_in_effect(now)),
        ),
        JewishCalendarBinarySensorEntityDescription(
            key="erev_shabbat_hag",
            translation_key="erev_shabbat_hag",
            is_on=lambda state, now: bool(state.erev_shabbat_chag(now)),
            entity_registry_enabled_default=False, # Disabled by default
        ),
        # ...
    )
    ```

The selection of which entities are enabled versus disabled by default appears to align well with the rule's intent of providing core functionality by default while making less universally critical or more numerous/detailed entities opt-in. This prevents overwhelming the user with too many entities upon initial setup.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:26:24. Prompt tokens: 13514, Output tokens: 1394, Total tokens: 19241_
