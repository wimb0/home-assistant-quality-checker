# evohome: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [evohome](https://www.home-assistant.io/integrations/evohome/) |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates)                                                     |
| Status | **todo**                                                                 |

## Overview

The `parallel-updates` rule requires integrations to explicitly specify the number of parallel updates and actions that can be sent to a device or service. This is particularly important for cloud-based services to prevent overwhelming the API with too many concurrent requests.

The `evohome` integration interacts with the Honeywell Total Connect Comfort cloud API and provides `climate` and `water_heater` platforms. These platforms involve both fetching state data and sending action commands (e.g., setting temperature, changing mode). Therefore, the `parallel-updates` rule applies to this integration.

Currently, the `evohome` integration does not define the `PARALLEL_UPDATES` constant in its platform files:
*   `homeassistant/components/evohome/climate.py`
*   `homeassistant/components/evohome/water_heater.py`

While the integration uses a `DataUpdateCoordinator` (`EvoDataUpdateCoordinator`), which centralizes data *fetching* (updates), the `PARALLEL_UPDATES` setting also governs the parallelism of *action calls* (service calls like setting temperature or mode). The rule states: "When using a coordinator... only the action calls will be relevant to consider for setting an appropriate number of parallel updates." Since `climate` and `water_heater` entities are not read-only and support actions, `PARALLEL_UPDATES` should be explicitly set to an appropriate value to manage the concurrency of these actions.

Without `PARALLEL_UPDATES` being defined, Home Assistant will use a default value (which can be >1), potentially leading to multiple concurrent action calls to the evohome API if, for example, an automation triggers changes to several entities simultaneously. This could lead to API rate-limiting or other issues.

## Suggestions

To comply with the `parallel-updates` rule and ensure robust interaction with the cloud API, the `PARALLEL_UPDATES` constant should be added to both platform files.

1.  **In `homeassistant/components/evohome/climate.py`:**
    Add the following line at the top of the file (e.g., after imports):
    ```python
    PARALLEL_UPDATES = 1
    ```

2.  **In `homeassistant/components/evohome/water_heater.py`:**
    Add the following line at the top of the file (e.g., after imports):
    ```python
    PARALLEL_UPDATES = 1
    ```

**Reasoning for `PARALLEL_UPDATES = 1`:**

*   **Explicitly Sets Parallelism:** This fulfills the rule's requirement to explicitly define the number of parallel updates/actions.
*   **Safe Default for Cloud APIs:** Setting `PARALLEL_UPDATES = 1` ensures that Home Assistant will dispatch service calls (actions) to `evohome` climate and water_heater entities one at a time. This serializes the commands sent to the Honeywell TCC API, which is a safer approach for cloud services that might have rate limits or be sensitive to concurrent commands.
*   **Coordinator Context:** While the `DataUpdateCoordinator` handles the polling for entity state updates in a centralized manner, this setting will primarily control the concurrency of actions (e.g., `set_temperature`, `set_hvac_mode`, `set_operation_mode`) initiated by the user or automations.
*   **Alternative Values:** If the `evohome` API is known to robustly handle a higher number of concurrent *action* requests without issues, this value could be increased (e.g., `2`, `3`, or `0` for HA's default unlimited). However, `1` is a conservative and widely accepted value for ensuring stability with external APIs unless proven otherwise.

By implementing these changes, the `evohome` integration will explicitly manage the parallelism of requests to its backend, adhering to the `parallel-updates` quality scale rule and potentially improving its reliability.

---

_Created at 2025-05-29 12:47:28. Prompt tokens: 21790, Output tokens: 963, Total tokens: 25800._

_Report based on [`7334aa4`](https://github.com/home-assistant/core/tree/7334aa48f1e12289b3236f0b424a0fc16f5c2b6e)._

_AI can be wrong. Always verify the report and the code against the rule._
