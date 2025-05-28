# overkiz: async-dependency

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [overkiz](https://www.home-assistant.io/integrations/overkiz/) |
| Rule   | [async-dependency](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/async-dependency)                                                     |
| Status | **done**                                                                 |

## Overview

The `async-dependency` rule requires that external libraries used by an integration are asynchronous to work efficiently with Home Assistant's asyncio event loop. This rule applies to the `overkiz` integration as it utilizes the `pyoverkiz` library, specified in its `manifest.json`:
```json
  "requirements": ["pyoverkiz==1.17.1"],
```

The `overkiz` integration fully follows this rule. The `pyoverkiz` library is an asyncio-based library, and the integration uses it in an asynchronous manner.

This is evidenced by several key aspects of the code:

1.  **Asynchronous Client Initialization**: The `OverkizClient` from `pyoverkiz` is instantiated with an `aiohttp.ClientSession` created by `homeassistant.helpers.aiohttp_client.async_create_clientsession`. This is the standard Home Assistant practice for HTTP-based async libraries. This can be seen in `homeassistant/components/overkiz/__init__.py`:
    ```python
    # In homeassistant/components/overkiz/__init__.py

    def create_local_client(
        hass: HomeAssistant, host: str, token: str, verify_ssl: bool
    ) -> OverkizClient:
        """Create Overkiz local client."""
        session = async_create_clientsession(hass, verify_ssl=verify_ssl) # Correctly gets async session

        return OverkizClient(
            username="",
            password="",
            token=token,
            session=session, # Passes session to the library client
            server=generate_local_server(host=host),
            verify_ssl=verify_ssl,
        )

    def create_cloud_client(
        hass: HomeAssistant, username: str, password: str, server: OverkizServer
    ) -> OverkizClient:
        """Create Overkiz cloud client."""
        session = async_create_clientsession(hass) # Correctly gets async session

        return OverkizClient(
            username=username, password=password, session=session, server=server # Passes session to the library client
        )
    ```

2.  **Asynchronous Library Calls**: All interactions with the `pyoverkiz` client methods throughout the integration's codebase are performed using `await`. This indicates that the library methods are coroutines and are being called in a non-blocking way. Examples include:
    *   In `homeassistant/components/overkiz/__init__.py` (e.g., line 74-79):
        ```python
        await client.login()
        setup = await client.get_setup()
        # ...
        if api_type == APIType.CLOUD:
            scenarios = await client.get_scenarios()
        ```
    *   In `homeassistant/components/overkiz/coordinator.py` (e.g., line 62):
        ```python
        events = await self.client.fetch_events()
        ```
    *   In `homeassistant/components/overkiz/executor.py` (e.g., line 58):
        ```python
        exec_id = await self.coordinator.client.execute_command(
            self.device.device_url,
            Command(command_name, parameters),
            "Home Assistant",
        )
        ```
    *   In `homeassistant/components/overkiz/config_flow.py` (e.g., line 63):
        ```python
        await client.login(register_event_listener=False)
        ```

This consistent use of `async` and `await` with the `pyoverkiz` library, along with the proper injection of an `aiohttp.ClientSession`, confirms that the dependency is being handled asynchronously as per the rule's requirements.

## Suggestions

No suggestions needed.

_Created at 2025-05-28 12:48:34. Prompt tokens: 86686, Output tokens: 982, Total tokens: 90210_
