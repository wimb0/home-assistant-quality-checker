# jewish_calendar: discovery-update-info

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [discovery-update-info](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery-update-info)                                                     |
| Status | **exempt**                                       |
| Reason | The integration is of `iot_class: calculated` and does not perform network discovery of devices or services. It relies on user-configured location and time data. |

## Overview

The `discovery-update-info` rule requires integrations that use discovery mechanisms (like mDNS, SSDP, DHCP) to update the network information (e.g., IP address) of previously configured devices if they are rediscovered with new network details.

The `jewish_calendar` integration does not apply to this rule.
1.  **No Network Discovery:** The `manifest.json` for `jewish_calendar` does not declare any discovery protocols (e.g., `zeroconf`, `ssdp`, `dhcp`).
    ```json
    {
      "domain": "jewish_calendar",
      "name": "Jewish Calendar",
      "codeowners": ["@tsvi"],
      "config_flow": true,
      "documentation": "https://www.home-assistant.io/integrations/jewish_calendar",
      "iot_class": "calculated",
      "loggers": ["hdate"],
      "requirements": ["hdate[astral]==1.1.0"],
      "single_config_entry": true
    }
    ```
2.  **Calculated IoT Class:** The `iot_class` is specified as `"calculated"`. This indicates that the integration primarily performs calculations based on existing data (like Home Assistant's configured location, time, or user-provided settings) rather than interacting with or discovering external network devices or services.
3.  **Configuration Flow:** The `config_flow.py` only implements `async_step_user` and `async_step_reconfigure`. It does not include any discovery-related steps (e.g., `async_step_zeroconf`). The configuration relies on user input for location (latitude, longitude), elevation, time zone, language, and diaspora status. It does not involve discovering or connecting to any network-based device or service whose IP address might change.

The rule's exception states: "Integrations where the devices can't be discovered are exempt from this rule." Since the `jewish_calendar` integration does not discover any devices or services that would have changeable network information, it is exempt from this rule. There is no discovered network information to update.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:22:49. Prompt tokens: 13647, Output tokens: 632, Total tokens: 15107_
