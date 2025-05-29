# evohome: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **done**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `appropriate-polling` rule applies to this integration because its `manifest.json` specifies `"iot_class": "cloud_polling"`, indicating it polls a cloud service for data.

The integration **follows** this rule. Here's how:

1.  **Polling Mechanism:** The integration uses a `DataUpdateCoordinator` (class `EvoDataUpdateCoordinator` in `coordinator.py`). This is the recommended approach for managing polling and data updates.

2.  **Configurable Polling Interval:** The `update_interval` for the `EvoDataUpdateCoordinator` is set during its initialization using a value from the configuration entry's options:
    ```python
    # homeassistant/components/evohome/coordinator.py
    class EvoDataUpdateCoordinator(DataUpdateCoordinator):
        # ...
        def __init__(
            self,
            # ...
        ) -> None:
            """Class to manage fetching data."""

            super().__init__(
                hass,
                logger,
                config_entry=config_entry,
                name=name,
                update_interval=timedelta(seconds=config_entry.options[CONF_SCAN_INTERVAL]),
            )
            # ...
    ```
    This allows the polling interval to be user-configurable.

3.  **Default Polling Interval:**
    *   For new installations set up via the UI, the default polling interval is 5 minutes (300 seconds). This is defined by `DEFAULT_SCAN_INTERVAL` in `const.py` and used in `DEFAULT_OPTIONS` in `config_flow.py`.
        ```python
        # homeassistant/components/evohome/const.py
        DEFAULT_SCAN_INTERVAL: Final = 60 * 5  # 300 seconds
        ```
        ```python
        # homeassistant/components/evohome/config_flow.py
        DEFAULT_OPTIONS: Final[EvoOptionDataT] = {
            CONF_HIGH_PRECISION: DEFAULT_HIGH_PRECISION,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL, # 300 seconds
        }
        ```
    *   For configurations imported from `configuration.yaml`, if `scan_interval` was not specified, it also defaulted to 5 minutes as per the `CONFIG_SCHEMA` in `__init__.py`.

4.  **Appropriateness of the Interval:** A default polling interval of 5 minutes for a cloud-based heating control system like Evohome is generally considered appropriate. It balances the need for reasonably up-to-date information (temperatures, setpoints, mode) with the need to be considerate of the cloud API's rate limits. The data from a heating system does not typically change on a second-by-second basis, making very frequent polling unnecessary and potentially problematic.

5.  **User Configuration and Guidance:**
    *   Users can customize the polling interval via the integration's options flow.
    *   The options flow (`EvoOptionsFlowHandler` in `config_flow.py`) guides users to a sensible range, typically between 3 minutes (`MINIMUM_SCAN_INTERVAL`) and 15 minutes (`MAXIMUM_SCAN_INTERVAL`), with 5 minutes as the suggested default.
        ```python
        # homeassistant/components/evohome/config_flow.py
        # In EvoOptionsFlowHandler.async_step_init:
        default_scan_interval = max(
            (DEFAULT_SCAN_INTERVAL, self._options[CONF_SCAN_INTERVAL]) # Suggests 300s or current if higher
        )
        minimum_scan_interval = min(
            (MINIMUM_SCAN_INTERVAL, self._options[CONF_SCAN_INTERVAL]) # Enforces 180s or current if lower (but respects even lower legacy values)
        )
        # ...
        vol.Optional(
            CONF_SCAN_INTERVAL,
            default=default_scan_interval,
        ): vol.All(
            NumberSelector(
                NumberSelectorConfig(
                    max=MAXIMUM_SCAN_INTERVAL,         # 900 seconds (15 minutes)
                    min=minimum_scan_interval,         # Typically 180 seconds (3 minutes)
                    step=15,
                    mode=NumberSelectorMode.SLIDER,
                ),
            ),
        ),
        ```
    *   The integration also includes error handling for API rate limits (`HTTPStatus.TOO_MANY_REQUESTS` in `coordinator.py`), which would prompt users to consider increasing their scan interval if issues arise.

The combination of a reasonable default polling interval (5 minutes), user configurability within a guided range, and awareness of API limitations demonstrates that the integration responsibly manages polling as per the rule's intent.

## Suggestions

No suggestions needed.

---

_Created at 2025-05-29 11:41:48. Prompt tokens: 21983, Output tokens: 1188, Total tokens: 26873._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
