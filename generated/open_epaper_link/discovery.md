# open_epaper_link: discovery

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [open_epaper_link](https://github.com/OpenEPaperLink/Home_Assistant_Integration) |
| Rule   | [discovery](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/discovery)                                                     |
| Status | **todo**                                       |
| Reason |                                                                          |

## Overview

The `discovery` rule requires integrations to support automatic discovery of devices if the devices themselves have this capability (e.g., via mDNS, SSDP, Bluetooth, DHCP, etc.). This enhances user experience by simplifying the setup process.

The `open_epaper_link` integration connects to an OpenEPaperLink Access Point (AP), which is a network-connected device (typically an ESP32). Such devices are prime candidates for network discovery protocols like mDNS (Zeroconf) or SSDP.

Currently, the integration does not implement any discovery mechanisms:
1.  The `manifest.json` file (relevant content below) does not declare support for any discovery protocols (e.g., `zeroconf`, `ssdp`).
    ```json
    {
      "domain": "open_epaper_link",
      "name": "OpenEPaperLink",
      "config_flow": true,
      "integration_type": "hub",
      "iot_class": "local_push",
      "requirements": [
        "qrcode[pil]==7.4.2",
        "requests_toolbelt==1.0.0",
        "websocket-client==1.7.0",
        "websockets==14.2"
      ],
      "single_config_entry": true
    }
    ```

2.  The `config_flow.py` file only implements `async_step_user`, which requires the user to manually input the IP address or hostname of the AP. There are no discovery-specific steps like `async_step_zeroconf` or `async_step_ssdp`.
    ```python
    # homeassistant/components/open_epaper_link/config_flow.py
    STEP_USER_DATA_SCHEMA = vol.Schema(
        {
            vol.Required(CONF_HOST): str,
        }
    )

    # ...

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ):
        """Handle the initial step of the config flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # _validate_input uses the provided host
            info, error_tuple_part = await self._validate_input(user_input[CONF_HOST])
            # In the actual code, _validate_input returns (dict, error_string),
            # this is simplified for brevity.
            error = error_tuple_part # Assuming error_tuple_part is the error string
            if not error:
                # Current unique_id is set to the host IP, which is not stable
                await self.async_set_unique_id(self._host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={CONF_HOST: self._host}
                )
            errors["base"] = error
        # ...
    ```

Since the OpenEPaperLink AP is a network device, it is reasonable to expect it could be discoverable. Therefore, the rule applies, and the integration currently does not follow it.

## Suggestions

To make the `open_epaper_link` integration compliant with the `discovery` rule, the following changes are recommended, focusing on mDNS (Zeroconf) discovery as it's common for ESP32-based devices:

1.  **AP Firmware Enhancement (Coordination Required):**
    *   The OpenEPaperLink AP firmware should be updated to broadcast an mDNS service (e.g., `_openepaperlink._tcp.local.`).
    *   This mDNS service advertisement (TXT records) should include a stable unique identifier for the AP, ideally its Wi-Fi MAC address (e.g., `stationmac=AA:BB:CC:DD:EE:FF`). The `/sysinfo` endpoint on the AP already provides `stationmac`.

2.  **Update `manifest.json`:**
    Add the `zeroconf` key to declare the mDNS service type the integration will listen for.
    ```json
    // homeassistant/components/open_epaper_link/manifest.json
    {
      "domain": "open_epaper_link",
      "name": "OpenEPaperLink",
      "codeowners": [
        "@jonasniesner"
      ],
      "config_flow": true,
      "dependencies": [
        "recorder"
      ],
      "documentation": "https://github.com/jonasniesner/open_epaper_link_homeassistant",
      "integration_type": "hub",
      "iot_class": "local_push",
      "issue_tracker": "https://github.com/jonasniesner/open_epaper_link_homeassistant/issues",
      "requirements": [
        "qrcode[pil]==7.4.2",
        "requests_toolbelt==1.0.0",
        "websocket-client==1.7.0",
        "websockets==14.2"
      ],
      "single_config_entry": true,
      "version": "1.0.0",
      "zeroconf": [
        "_openepaperlink._tcp.local."
      ]
    }
    ```

3.  **Enhance `config_flow.py` for Stable Unique ID:**
    *   Modify `_validate_input` to fetch the AP's MAC address (e.g., from the `/sysinfo` endpoint which contains `stationmac`) and return it.
    *   In `async_step_user`, use this MAC address for `await self.async_set_unique_id(ap_mac)` instead of the host IP. This makes the unique ID stable across IP changes. The `_abort_if_unique_id_configured(updates={CONF_HOST: self._host})` call will then correctly update the IP if it changes.

    Example modification sketch for `_validate_input` and `async_step_user`:
    ```python
    # homeassistant/components/open_epaper_link/config_flow.py

    # Modified _validate_input to return (info, error_str, ap_mac_str | None)
    async def _validate_input(self, host: str) -> tuple[dict[str, str], str | None, str | None]:
        # ... (existing validation logic)
        # After successful initial connection:
        try:
            session = async_get_clientsession(self.hass) # Ensure session is available
            async with asyncio.timeout(10):
                async with session.get(f"http://{host}/sysinfo") as sysinfo_response:
                    if sysinfo_response.status == 200:
                        sysinfo_data = await sysinfo_response.json()
                        ap_mac = sysinfo_data.get("stationmac")
                        if not ap_mac:
                            _LOGGER.error("Could not retrieve MAC address from AP at %s via /sysinfo", host)
                            return {}, "cannot_get_mac", None
                        self._host = host # Keep storing host for data
                        return {"title": f"OpenEPaperLink AP ({host})"}, None, ap_mac.lower()
                    _LOGGER.error("Failed to get /sysinfo from %s: status %d", host, sysinfo_response.status)
                    return {}, "cannot_get_mac", None # Or a more specific error
        except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
            _LOGGER.warning("Error fetching /sysinfo from %s: %s", host, exc)
            return {}, "cannot_connect_sysinfo", None # Or existing "cannot_connect"
        # ... (rest of original error handling)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            info, error, ap_mac = await self._validate_input(user_input[CONF_HOST])
            if not error and ap_mac:
                await self.async_set_unique_id(ap_mac) # Use MAC as unique ID
                self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})
                return self.async_create_entry(
                    title=info["title"],
                    data={CONF_HOST: self._host} # Store host IP in data
                )
            errors["base"] = error if error else "unknown"
        # ... (rest of the method)
    ```

4.  **Implement `async_step_zeroconf` in `config_flow.py`:**
    Add a new method to handle discovered mDNS services.
    ```python
    # homeassistant/components/open_epaper_link/config_flow.py
    import aiohttp # Add if not already imported
    import asyncio # Add if not already imported
    from homeassistant.components import zeroconf
    from homeassistant.const import CONF_HOST
    from homeassistant.data_entry_flow import FlowResult # Add if not already imported
    from homeassistant.helpers.aiohttp_client import async_get_clientsession # Add if not already imported

    # ... (inside ConfigFlow class)

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle discovery via zeroconf."""
        host = discovery_info.host
        # Assuming the AP firmware adds 'stationmac' to mDNS properties
        ap_mac = discovery_info.properties.get("stationmac")

        if not ap_mac:
            _LOGGER.info(
                "Discovered OpenEPaperLink AP at %s (%s) but 'stationmac' property missing in mDNS record. "
                "Attempting to fetch from /sysinfo.",
                host, discovery_info.name
            )
            # Fallback: try to fetch MAC from /sysinfo if not in mDNS properties
            # This reuses parts of the modified _validate_input logic
            session = async_get_clientsession(self.hass)
            try:
                async with asyncio.timeout(10):
                    async with session.get(f"http://{host}/sysinfo") as sysinfo_response:
                        if sysinfo_response.status == 200:
                            sysinfo_data = await sysinfo_response.json()
                            ap_mac = sysinfo_data.get("stationmac")
                            if not ap_mac:
                                _LOGGER.warning("Could not retrieve MAC from %s /sysinfo during discovery.", host)
                                return self.async_abort(reason="cannot_get_mac")
                        else:
                            _LOGGER.warning("Failed to get /sysinfo from %s (status %s) during discovery.", host, sysinfo_response.status)
                            return self.async_abort(reason="cannot_connect") # Or cannot_get_mac
            except (asyncio.TimeoutError, aiohttp.ClientError):
                _LOGGER.warning("Connection error fetching /sysinfo from %s during discovery.", host)
                return self.async_abort(reason="cannot_connect")
            except Exception:
                _LOGGER.exception("Unexpected error fetching /sysinfo from %s during discovery.", host)
                return self.async_abort(reason="unknown")

        await self.async_set_unique_id(ap_mac.lower())
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        # Store context for the confirmation step
        self.context["host"] = host
        # Use a descriptive name, e.g., from mDNS service name or AP alias if available
        self.context["title_placeholders"] = {"name": discovery_info.name.replace("._openepaperlink._tcp.local.", "")}

        # Perform a basic validation that the AP is responsive (similar to example in rule)
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(f"http://{host}") as response:
                    if response.status != 200:
                        return self.async_abort(reason="cannot_connect")
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return self.async_abort(reason="cannot_connect")
        except Exception:
            _LOGGER.exception("Unexpected validation error during zeroconf for %s", host)
            return self.async_abort(reason="unknown")

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user confirmation of a discovered device."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.context["title_placeholders"]["name"], # Or a more specific title
                data={CONF_HOST: self.context["host"]},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders=self.context["title_placeholders"],
        )
    ```

By implementing these changes, the `open_epaper_link` integration would allow users to discover their APs automatically, improving the setup experience and robustness against IP address changes.

_Created at 2025-05-14 20:57:55. Prompt tokens: 61068, Output tokens: 3235, Total tokens: 69875_
