# wled: config-flow-test-coverage

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [config-flow-test-coverage](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow-test-coverage)                                                     |
| Status | **todo**                                       |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `config-flow-test-coverage` rule applies to the `wled` integration because it defines a configuration flow (`config_flow: true` in `manifest.json` and a `config_flow.py` file). This rule mandates **100% test coverage** for all aspects of the config flow, including user-initiated setup, discovery flows (like Zeroconf), options flows, reauthentication, and reconfiguration flows. Crucially, tests must verify error recovery and ensure the uniqueness of configuration entries.

The `wled` integration's `config_flow.py` implements:
1.  **User-initiated flow (`async_step_user`):** Allows users to add WLED devices by providing a hostname. It includes logic to connect to the device and handle potential `WLEDConnectionError`.
2.  **Zeroconf discovery flow (`async_step_zeroconf`, `async_step_zeroconf_confirm`):** Allows discovery of WLED devices on the network. It also handles connection attempts and potential errors.
3.  **Unique ID check:** Both user and Zeroconf flows use the device's MAC address as a unique ID to prevent duplicate configurations, utilizing `self.async_set_unique_id()` and `self._abort_if_unique_id_configured()`.
4.  **Options flow (`WLEDOptionsFlowHandler`):** Allows users to configure the `CONF_KEEP_MAIN_LIGHT` option after the initial setup. This also serves as a reconfiguration flow for this specific option.

While the `config_flow.py` includes error handling (e.g., showing a "cannot_connect" error for user flow, aborting for Zeroconf connection issues) and uniqueness checks, the rule requires these paths to be explicitly tested. Without the `tests/components/wled/test_config_flow.py` file provided, it is assumed that 100% test coverage for all these scenarios, including error recovery steps (e.g., successfully setting up after an initial connection failure) and explicit tests for preventing duplicate entries, has not been achieved.

The existing config flow does not define a reauthentication flow, so tests for it are not applicable to the current codebase.

## Suggestions

To comply with the `config-flow-test-coverage` rule, a comprehensive test suite should be created in `tests/components/wled/test_config_flow.py`. This suite must aim for 100% line and branch coverage of `config_flow.py`.

Key scenarios to test include:

**General Setup for Tests:**
*   Mock the `wled.WLED` client, particularly the `wled.update()` method, to simulate successful connections (returning a mock `Device` object with predefined `info.mac_address` and `info.name`) and connection failures (raising `WLEDConnectionError`).
*   Use `pytest_homeassistant_custom_component.common.MockConfigEntry` for testing options flows and already_configured scenarios.
*   Leverage `hass.config_entries.flow.async_init` and `hass.config_entries.flow.async_configure`.

**1. User-Initiated Flow (`async_step_user`):**
    *   **Happy Path:**
        *   Test successful setup with a valid host.
        *   Assert `FlowResultType.CREATE_ENTRY`, and check `title` and `data` of the created entry.
    *   **Connection Error & Recovery:**
        *   Test providing a host that results in `WLEDConnectionError` (mock `_async_get_device` to raise it).
        *   Assert `FlowResultType.FORM` is returned with `errors={"base": "cannot_connect"}`.
        *   Test that after the initial error, the user can input a correct host in the subsequent step and successfully complete the setup.
    *   **Already Configured:**
        *   Test attempting to add a WLED device (identified by its MAC address) that has already been configured.
        *   Assert `FlowResultType.ABORT` with `reason="already_configured"`.

**2. Zeroconf Discovery Flow (`async_step_zeroconf`, `async_step_zeroconf_confirm`):**
    *   **Happy Path:**
        *   Simulate a Zeroconf discovery (mock `ZeroconfServiceInfo` with and without `CONF_MAC` in properties).
        *   Test successful connection and entry creation.
        *   Assert `FlowResultType.CREATE_ENTRY` (or `FORM` for confirm step), and check `title` and `data`.
    *   **Connection Error:**
        *   Simulate Zeroconf discovery where the `_async_get_device` call fails with `WLEDConnectionError`.
        *   Assert `FlowResultType.ABORT` with `reason="cannot_connect"`.
    *   **Already Configured:**
        *   Test Zeroconf discovery for a device whose MAC address (either from properties or fetched) matches an existing config entry.
        *   Assert `FlowResultType.ABORT` with `reason="already_configured"`.
    *   **Confirmation Step Logic:**
        *   Test the `async_step_zeroconf_confirm` path where `onboarding.async_is_onboarded(self.hass)` is `False` (should create entry directly).
        *   Test the path where `onboarding.async_is_onboarded(self.hass)` is `True` (should show form), then submit the form to create the entry.

**3. Options Flow (`WLEDOptionsFlowHandler`):**
    *   **Show Form:**
        *   Initiate the options flow for an existing config entry.
        *   Assert `FlowResultType.FORM` is shown, and the schema correctly reflects the `CONF_KEEP_MAIN_LIGHT` option with its current or default value.
    *   **Submit Options:**
        *   Test submitting the options form with a new value for `CONF_KEEP_MAIN_LIGHT`.
        *   Assert `FlowResultType.CREATE_ENTRY` (which, for options flow, means updated options) and verify the updated options data.

**Example Snippet (Conceptual for User Flow Error):**
```python
# In tests/components/wled/test_config_flow.py
from unittest.mock import patch

from wled import WLEDConnectionError

from homeassistant.components.wled.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

async def test_user_flow_cannot_connect(hass: HomeAssistant) -> None:
    """Test user flow when connection fails."""
    with patch(
        "homeassistant.components.wled.config_flow.WLED._async_update", # Adjust target if _async_get_device calls wled.update() directly
        side_effect=WLEDConnectionError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.2.3.4"}
        )
        assert result2["type"] is FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}

# ... then add a test for recovery:
async def test_user_flow_cannot_connect_then_success(hass: HomeAssistant, mock_wled_device, mock_setup_entry) -> None:
    """Test user flow recovers after a connection error."""
    with patch(
        "homeassistant.components.wled.config_flow.WLED.update", # Assuming WLEDFlowHandler._async_get_device uses wled.update()
        side_effect=WLEDConnectionError,
    ) as mock_update:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_HOST: "bad-host"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}

        # Simulate user correcting the host
        mock_update.side_effect = None  # Clear the side effect
        mock_update.return_value = mock_wled_device # mock_wled_device is a fixture returning a valid Device object

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "good-host.local"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == mock_wled_device.info.name
    assert result2["data"] == {CONF_HOST: "good-host.local"}
    assert len(mock_setup_entry.mock_calls) == 1
```

By implementing these tests, the `wled` integration can ensure its config flow is robust, user-friendly, and meets the quality standards for 100% test coverage.

_Created at 2025-05-10 19:26:16. Prompt tokens: 22134, Output tokens: 2258, Total tokens: 27502_
