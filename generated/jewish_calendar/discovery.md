# jewish_calendar: discovery

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [jewish_calendar](https://www.home-assistant.io/integrations/jewish_calendar/) |
| Rule   | [discovery](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery)                                                     |
| Status | **exempt**                                       |
| Reason | The `jewish_calendar` integration is a "calculated" integration that computes calendar information based on user-configured location and time. It does not interact with discoverable physical devices or network services. |

## Overview

The `discovery` rule mandates that integrations should support discovery mechanisms (like mDNS, SSDP, Bluetooth, etc.) if their corresponding devices or services are discoverable, to enhance user experience by simplifying setup.

This rule does **not apply** to the `jewish_calendar` integration. Here's why:

1.  **Nature of the Integration:** The `jewish_calendar` integration is fundamentally a "calculated" integration. Its primary purpose is to compute Jewish calendar dates, holidays, and Zmanim (religious times) based on geographical location (latitude, longitude, elevation), time zone, and user-defined preferences (e.g., Diaspora status, candle lighting offsets). This is explicitly stated in its `manifest.json` with `"iot_class": "calculated"`.

    ```json
    // homeassistant/components/jewish_calendar/manifest.json
    {
      "domain": "jewish_calendar",
      "name": "Jewish Calendar",
      // ...
      "iot_class": "calculated",
      // ...
    }
    ```

2.  **No External Device/Service:** The integration does not communicate with or control any physical device or network service that could be discovered using mechanisms like mDNS, SSDP, Bluetooth, USB, or DHCP. All its data is derived from calculations performed by the `hdate` library using configuration parameters.

3.  **Configuration Method:** The integration is configured via a config flow (`config_flow.py`), which involves the user manually providing location details (or using Home Assistant's default location) and other preferences. There are no discovery steps (e.g., `async_step_zeroconf`, `async_step_ssdp`) present in the `config_flow.py`, which is consistent with its non-discoverable nature.

    ```python
    // homeassistant/components/jewish_calendar/config_flow.py
    class JewishCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
        # ...
        async def async_step_user(
            self, user_input: dict[str, Any] | None = None
        ) -> ConfigFlowResult:
            """Handle the initial step."""
            # ... (logic for manual user input)
    ```

4.  **Rule Exception:** The `discovery` rule itself includes an exception: "Integrations where the devices can't be discovered are exempt from this rule." The `jewish_calendar` integration falls squarely into this category as there is no "device" or "service" in the traditional sense to be discovered.

Therefore, the `jewish_calendar` integration is exempt from the `discovery` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-29 08:22:31. Prompt tokens: 14046, Output tokens: 732, Total tokens: 15945_
