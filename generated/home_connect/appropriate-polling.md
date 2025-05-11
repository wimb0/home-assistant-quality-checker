# home_connect: appropriate-polling

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [appropriate-polling](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling)                                                     |
| Status | **todo**                                       |

## Overview

The `appropriate-polling` rule applies to this integration because `home_connect` utilizes `DataUpdateCoordinator` for periodic data fetching, which constitutes polling. Specifically, the `HomeConnectCoordinator` class in `coordinator.py` inherits from `DataUpdateCoordinator` and implements the `_async_update_data` method to refresh appliance data.

The integration currently does **not fully follow** this rule for the following reasons:

1.  **No Explicit Polling Interval Set:** The `HomeConnectCoordinator` does not explicitly define an `update_interval` in its `__init__` method.
    ```python
    # coordinator.py
    class HomeConnectCoordinator(
        DataUpdateCoordinator[dict[str, HomeConnectApplianceData]]
    ):
        # ...
        def __init__(
            self,
            hass: HomeAssistant,
            config_entry: HomeConnectConfigEntry,
            client: HomeConnectClient,
        ) -> None:
            """Initialize."""
            super().__init__(
                hass,
                _LOGGER,
                config_entry=config_entry,
                name=config_entry.entry_id,
                # No update_interval is explicitly passed here
            )
            # ...
    ```
    Consequently, it defaults to the `DataUpdateCoordinator`'s standard interval of 1 minute (`timedelta(seconds=60)`). The rule implies that the polling interval should be an active, considered choice by the developer.

2.  **Potentially Inappropriate Default Interval for a Push-Based Integration:** The `home_connect` integration is primarily push-based, as indicated by its `iot_class: "cloud_push"` in `manifest.json` and the use of an event stream (`self.client.stream_all_events()`) in `coordinator.py`'s `_event_listener` method.
    For such integrations, the periodic polling performed by the `DataUpdateCoordinator` typically serves secondary roles, such as:
    *   Discovering new or re-paired appliances.
    *   Acting as a fallback mechanism if the push stream misses updates or fails.
    *   Performing a full state synchronization.

    The `_async_update_data` method performs a full refresh for all appliances by calling `_get_appliance_data`, which in turn calls multiple API endpoints per appliance (e.g., `get_settings`, `get_status`, `get_all_programs`, `get_available_commands`). Performing such a comprehensive fetch for all connected appliances every 1 minute might be unnecessarily frequent and could contribute to hitting API rate limits, especially when a real-time event stream is already active. A longer interval for this full refresh (e.g., 5-15 minutes) would likely be more "appropriate" and "responsible," reducing the load on the Home Connect API and Home Assistant. The integration already includes logic to handle `TooManyRequestsError` (e.g., in `_async_update_data`), suggesting that API rate limits are a concern.

While a 1-minute interval is sometimes acceptable, the combination of relying on a default and the primary push-based nature of the integration suggests that the current polling strategy for the full refresh may not be optimally "appropriate."

## Suggestions

To make the `home_connect` integration compliant with the `appropriate-polling` rule, consider the following:

1.  **Explicitly Set `update_interval`:**
    Modify the `HomeConnectCoordinator.__init__` method in `coordinator.py` to explicitly pass an `update_interval` to the `super().__init__()` call.

    Example:
    ```python
    # coordinator.py
    from datetime import timedelta # Add timedelta import if not already present

    class HomeConnectCoordinator(
        DataUpdateCoordinator[dict[str, HomeConnectApplianceData]]
    ):
        # ...
        def __init__(
            self,
            hass: HomeAssistant,
            config_entry: HomeConnectConfigEntry,
            client: HomeConnectClient,
        ) -> None:
            """Initialize."""
            # Determine an appropriate interval, e.g., 5, 10, or 15 minutes
            # This is just an example, the actual value needs careful consideration.
            custom_update_interval = timedelta(minutes=10)

            super().__init__(
                hass,
                _LOGGER,
                config_entry=config_entry,
                name=config_entry.entry_id,
                update_interval=custom_update_interval, # Explicitly set interval
            )
            self.client = client
            # ...
    ```

2.  **Determine an "Appropriate" Interval:**
    Carefully evaluate and choose an interval for the periodic full refresh performed by `_async_update_data`. This interval should be longer than the current default of 1 minute if the event stream is reliable for most real-time status updates. Consider these factors:
    *   **Appliance Discovery:** How quickly do newly added or re-paired appliances need to be detected by this polling mechanism? (Note: `PAIRED` events are also handled by the event stream for more immediate discovery).
    *   **Fallback Reliability:** If the event stream fails or misses data, what is an acceptable delay for the polling mechanism to catch up with a full state sync?
    *   **API Rate Limits:** A longer interval significantly reduces the number of API calls made to the Home Connect cloud service, respecting rate limits and reducing overall system load.
    *   **Nature of Data:** The data fetched during the full refresh (settings, available programs/commands) often changes infrequently.
    *   **Common Practices:** For push-based integrations, intervals for secondary polling/full syncs are often in the range of 5 to 30 minutes.

3.  **Document Reasoning:**
    It's good practice to add a comment in the code or in the Pull Request explaining why the chosen `update_interval` is considered appropriate for this integration, considering its hybrid push/pull nature. This demonstrates that the interval was a deliberate choice.

By explicitly setting a well-reasoned, potentially longer, polling interval for the `DataUpdateCoordinator`, the integration will better align with the "appropriate-polling" rule, ensuring responsible use of the cloud API.

_Created at 2025-05-10 20:17:25. Prompt tokens: 139815, Output tokens: 1475, Total tokens: 146154_
