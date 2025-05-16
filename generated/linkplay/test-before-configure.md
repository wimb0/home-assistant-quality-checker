# linkplay: test-before-configure

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [linkplay](https://www.home-assistant.io/integrations/linkplay/) |
| Rule   | [test-before-configure](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-configure)                                                     |
| Status | **done**                                                                 |

## Overview

The `test-before-configure` rule requires that integrations test the connection to a device or service during the config flow, before a configuration entry is created. This is to ensure that issues like incorrect host, credentials, or network problems are caught early, improving the user experience.

This rule applies to the `linkplay` integration because:
1.  It uses a config flow (`config_flow: true` in `manifest.json` and `config_flow.py` is present).
2.  It connects to network-based LinkPlay devices, which can be subject to connectivity issues.
3.  It is not a helper integration and does not fall under the "runtime auto-discovery" exemption in the same way as integrations like Google Cast (where discovery might bypass an explicit pre-configuration test for *newly found* devices after initial setup). Linkplay's Zeroconf discovery initiates a config flow where connection testing is still relevant before creating an entry.

The `linkplay` integration **follows** this rule.

In `config_flow.py`, both the user-initiated setup (`async_step_user`) and the Zeroconf discovery flow (`async_step_zeroconf`) attempt to establish a connection and validate the device before creating a config entry.

1.  **User-initiated flow (`async_step_user`):**
    ```python
    # config_flow.py
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}
        if user_input:
            session: ClientSession = await async_get_client_session(self.hass)
            bridge: LinkPlayBridge | None = None

            try:
                bridge = await linkplay_factory_httpapi_bridge(
                    user_input[CONF_HOST], session
                )
            except LinkPlayRequestException:
                _LOGGER.exception(
                    "Failed to connect to LinkPlay device at %s", user_input[CONF_HOST]
                )
                errors["base"] = "cannot_connect"

            if bridge is not None: # This check is effectively 'if no exception occurred'
                # ... (set unique_id, create entry) ...
                return self.async_create_entry(
                    title=self.data[CONF_MODEL],
                    data={CONF_HOST: self.data[CONF_HOST]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )
    ```
    The call to `linkplay_factory_httpapi_bridge(user_input[CONF_HOST], session)` attempts to connect to the specified LinkPlay device. If this fails (e.g., host is incorrect, device is unreachable), a `LinkPlayRequestException` is caught. In this case, `errors["base"]` is set to `"cannot_connect"`, and the form is shown again to the user with an error message, preventing the creation of a non-functional config entry.

2.  **Zeroconf discovery flow (`async_step_zeroconf`):**
    ```python
    # config_flow.py
    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle Zeroconf discovery."""
        # ...
        try:
            bridge = await linkplay_factory_httpapi_bridge(discovery_info.host, session)
        except LinkPlayRequestException:
            _LOGGER.exception(
                "Failed to connect to LinkPlay device at %s", discovery_info.host
            )
            return self.async_abort(reason="cannot_connect")
        # ... (proceeds to discovery_confirm if successful) ...
    ```
    Similarly, during Zeroconf discovery, `linkplay_factory_httpapi_bridge` is called. If it fails with a `LinkPlayRequestException`, the flow is aborted with the reason `"cannot_connect"`. This also prevents a faulty entry from being created.

The function `linkplay_factory_httpapi_bridge` from the `python-linkplay` library is responsible for making the initial connection attempt. The fact that it can raise `LinkPlayRequestException` indicates it performs I/O and validates the device's accessibility. This is confirmed by its usage in `__init__.py`'s `async_setup_entry`, where the same exception leads to `ConfigEntryNotReady`.

Therefore, the integration correctly tests the connection before finalizing the configuration.

## Suggestions

No suggestions needed.

_Created at 2025-05-11 07:12:49. Prompt tokens: 11558, Output tokens: 1172, Total tokens: 14808_
