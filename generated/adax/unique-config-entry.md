# adax: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [adax](https://www.home-assistant.io/integrations/adax/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |
| Reason | N/A                                                                      |

## Overview

The `unique-config-entry` rule requires that an integration must prevent the same device or service from being set up multiple times. This is typically achieved by assigning a unique ID to the configuration entry or by matching specific data fields to detect existing entries.

This rule applies to the `adax` integration because it has a configuration flow (`config_flow: true` in `manifest.json` and a `config_flow.py` file), allowing users to set up Adax devices/accounts through the UI.

The `adax` integration **follows** this rule. It provides two methods for setting up Adax heaters: "Local" and "Cloud". For each method, it correctly ensures that a specific device (for local) or account (for cloud) cannot be configured more than once.

This is implemented in `config_flow.py`:

1.  **Local Connection (`async_step_local`)**:
    *   When configuring a device locally, the integration retrieves the device's MAC address.
    *   This MAC address is then used as the unique identifier for the config entry:
        ```python
        # homeassistant/components/adax/config_flow.py
        unique_id = str(configurator.mac_id)
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        ```
    *   If a config entry with the same MAC address (converted to string) already exists, `self._abort_if_unique_id_configured()` will raise an `AbortFlow` exception, preventing duplicate setup of the same local device. The user is typically shown an "already configured" message, corresponding to the `"already_configured": "[%key:common::config_flow::abort::already_configured_device%]"` entry in `strings.json`.

2.  **Cloud Connection (`async_step_cloud`)**:
    *   When configuring via the Adax cloud service, the user provides an `ACCOUNT_ID`.
    *   This `ACCOUNT_ID` is used as the unique identifier for the config entry:
        ```python
        # homeassistant/components/adax/config_flow.py
        await self.async_set_unique_id(str(user_input[ACCOUNT_ID]))
        self._abort_if_unique_id_configured()
        ```
    *   If a config entry with the same `ACCOUNT_ID` (converted to string) already exists, the setup is aborted, preventing the same cloud account from being added multiple times.

Both methods use the recommended pattern of `await self.async_set_unique_id()` followed by `self._abort_if_unique_id_configured()` to ensure the uniqueness of the configuration entry based on a relevant identifier (MAC address for local devices, Account ID for cloud services). This prevents duplicate entries for the same specific device (when added via local) or the same service account (when added via cloud).

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:10:27. Prompt tokens: 7286, Output tokens: 775, Total tokens: 11860_
