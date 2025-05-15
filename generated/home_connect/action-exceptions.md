# home_connect: action-exceptions

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [action-exceptions](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `action-exceptions` rule requires that service actions raise specific Home Assistant exceptions (`ServiceValidationError` for incorrect usage/input, and `HomeAssistantError` for internal errors like API communication failures) when they encounter problems. These exceptions should provide messages that can be shown to the user, ideally using translation keys.

The `home_connect` integration defines several services in `services.py`. This rule applies to the integration.

The integration correctly follows this rule:

1.  **Input Validation (`ServiceValidationError`):**
    *   Most service handlers utilize a helper function `_get_client_and_ha_id` (in `services.py`). This function checks for the existence of the device, config entry, and appliance ID. If any of these are not found (indicating incorrect input or a missing entity), it raises a `ServiceValidationError` with appropriate `translation_domain`, `translation_key`, and `translation_placeholders`. For example:
        ```python
        # homeassistant/components/home_connect/services.py
        async def _get_client_and_ha_id(
            hass: HomeAssistant, device_id: str
        ) -> tuple[HomeConnectClient, str]:
            device_registry = dr.async_get(hass)
            device_entry = device_registry.async_get(device_id)
            if device_entry is None:
                raise ServiceValidationError(  # Correctly raises ServiceValidationError
                    translation_domain=DOMAIN,
                    translation_key="device_entry_not_found",
                    translation_placeholders={
                        "device_id": device_id,
                    },
                )
            # ... similar checks for entry and ha_id
        ```
    *   The schema for the `SERVICE_SET_PROGRAM_AND_OPTIONS` service uses a validator `_require_program_or_at_least_one_option` which also raises a `ServiceValidationError` if the input data doesn't meet requirements:
        ```python
        # homeassistant/components/home_connect/services.py
        def _require_program_or_at_least_one_option(data: dict) -> dict:
            if ATTR_PROGRAM not in data and not any(
                option_key in data for option_key in (PROGRAM_ENUM_OPTIONS | PROGRAM_OPTIONS)
            ):
                raise ServiceValidationError( # Correctly raises ServiceValidationError
                    translation_domain=DOMAIN,
                    translation_key="required_program_or_one_option_at_least",
                )
            return data
        ```

2.  **API/Internal Errors (`HomeAssistantError`):**
    *   Service handlers that interact with the Home Connect API (e.g., `_async_service_program`, `async_service_setting`, `async_service_set_program_and_options`) wrap their API calls in `try...except HomeConnectError as err:` blocks.
    *   When a `HomeConnectError` (from the `aiohomeconnect` library) is caught, it is re-raised as a `HomeAssistantError`. These `HomeAssistantError` instances correctly use `translation_domain`, `translation_key`, `translation_placeholders`, and chain the original exception using `from err`. An example from `_async_service_program`:
        ```python
        # homeassistant/components/home_connect/services.py
        try:
            if start:
                await client.start_program(ha_id, program_key=program, options=options)
            else:
                await client.set_selected_program(
                    ha_id, program_key=program, options=options
                )
        except HomeConnectError as err:
            raise HomeAssistantError( # Correctly raises HomeAssistantError
                translation_domain=DOMAIN,
                translation_key="start_program" if start else "select_program",
                translation_placeholders={
                    **get_dict_from_home_connect_error(err),
                    "program": program,
                },
            ) from err
        ```
    This pattern is consistently applied across all service handlers in `services.py`.

3.  **Entity Action Methods:**
    While the rule specifically targets "Service actions", it's worth noting that similar robust error handling is also implemented in various entity methods that perform actions (e.g., `async_turn_on` for lights/switches, `async_set_native_value` for numbers, `async_press` for buttons). These methods also catch `HomeConnectError` and raise `HomeAssistantError` with translations, ensuring a consistent user experience. For example, in `light.py`:
    ```python
    # homeassistant/components/home_connect/light.py
    async def async_turn_on(self, **kwargs: Any) -> None:
        # ...
        try:
            await self.coordinator.client.set_setting(
                self.appliance.info.ha_id,
                setting_key=SettingKey(self.bsh_key),
                value=True,
            )
        except HomeConnectError as err:
            raise HomeAssistantError( # Correctly raises HomeAssistantError
                translation_domain=DOMAIN,
                translation_key="turn_on_light",
                translation_placeholders={
                    **get_dict_from_home_connect_error(err),
                    "entity_id": self.entity_id,
                },
            ) from err
        # ...
    ```

The integration correctly distinguishes between user input errors and internal/API errors, using the appropriate exception types and providing translated error messages.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 15:31:00. Prompt tokens: 136629, Output tokens: 1373, Total tokens: 140601_
