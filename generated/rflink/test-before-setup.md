# rflink: test-before-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [rflink](https://www.home-assistant.io/integrations/rflink/) |
| Rule   | [test-before-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup)                                                     |
| Status | **todo**                                                                 |

## Overview

The `test-before-setup` rule mandates that an integration, during its initialization, must verify if it can be set up correctly and promptly inform the user of any failures. For integrations like `rflink` that are configured via `configuration.yaml`, this implies that the `async_setup` function should return `False` if the initial setup (e.g., establishing a connection to the device) cannot be completed successfully.

The `rflink` integration currently does not fully adhere to this principle. Its `async_setup` function, located in `homeassistant/components/rflink/__init__.py`, initiates the connection to the RFLink device by creating an asynchronous task for the `connect()` coroutine:

```python
# In async_setup from homeassistant/components/rflink/__init__.py
    hass.async_create_task(connect(), eager_start=False)
    # ...
    return True
```

The `async_setup` function returns `True` immediately after dispatching this task, without awaiting the outcome of the connection attempt. The `connect()` coroutine is responsible for the actual connection:

```python
# In connect() from homeassistant/components/rflink/__init__.py
    async def connect():
        # ...
        try:
            async with asyncio.timeout(CONNECTION_TIMEOUT):
                transport, protocol = await connection # Connection attempt
        except (
            SerialException,
            OSError,
            TimeoutError,
        ):
            # ... logs error, schedules reconnect ...
            async_call_later(hass, reconnect_interval, _reconnect_job)
            return # Exits connect() on failure
        # ...
```

If the initial connection attempt within `connect()` fails, an error is logged, and a reconnection is scheduled. However, since `async_setup` has already returned `True`, Home Assistant considers the `rflink` integration to be successfully loaded, even if the primary RFLink gateway is unreachable at startup. Consequently, the user is not immediately informed of this setup failure through the standard Home Assistant mechanism (i.e., `async_setup` returning `False`), and the integration might appear loaded but be non-functional until a background reconnection attempt succeeds.

## Suggestions

To align with the `test-before-setup` rule, the `async_setup` function should await the initial connection attempt. If this attempt fails, `async_setup` should return `False`, clearly signaling to Home Assistant and the user that the integration could not be initialized.

1.  **Modify `async_setup` to await the initial connection and handle failures:**
    The `connect()` logic needs to be refactored so that `async_setup` can directly await its result and act accordingly.

    Here's a conceptual outline of changes in `homeassistant/components/rflink/__init__.py`:

    ```python
    # In homeassistant/components/rflink/__init__.py

    # ... (other imports and existing code like DATA_ENTITY_LOOKUP setup, service registration) ...

    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up the Rflink component."""
        # ... (existing setup for hass.data, services, event_callback definition) ...

        conf = config[DOMAIN]
        host = conf.get(CONF_HOST)
        port = conf[CONF_PORT]
        wait_for_ack = conf[CONF_WAIT_FOR_ACK]
        keepalive_idle_timer = conf[CONF_KEEPALIVE_IDLE]
        # ... (validate keepalive_idle_timer logic) ...
        reconnect_interval = conf[CONF_RECONNECT_INTERVAL]
        ignore_devices = conf[CONF_IGNORE_DEVICES]

        # Define event_callback, ensure it's available in this scope
        # @callback
        # def event_callback(event): ...

        # This callback is for disconnections *after* a successful initial setup
        # It will trigger the connect_and_reconnect_loop.
        @callback
        def schedule_reconnect_on_disconnect(_: Exception | None = None) -> None:
            """Schedule reconnect after connection has been unexpectedly lost."""
            RflinkCommand.set_rflink_protocol(None)
            async_dispatcher_send(hass, SIGNAL_AVAILABILITY, False)

            if hass.state is not CoreState.stopping:
                _LOGGER.warning(
                    "Disconnected from Rflink, attempting to reconnect in %s seconds",
                    reconnect_interval
                )
                hass.async_create_task(connect_and_reconnect_loop(), eager_start=False)

        async def try_connect_once():
            """Attempt to connect to Rflink once.
            Returns (transport, protocol) on success, raises exception on failure.
            """
            _LOGGER.debug("Attempting to connect to Rflink: host=%s, port=%s", host, port)
            connection = create_rflink_connection(
                port=port,
                host=host,
                keepalive=keepalive_idle_timer,
                event_callback=event_callback, # Assumed defined in async_setup
                disconnect_callback=schedule_reconnect_on_disconnect, # For later disconnections
                loop=hass.loop,
                ignore=ignore_devices,
            )
            async with asyncio.timeout(CONNECTION_TIMEOUT):
                transport, protocol = await connection
            return transport, protocol

        async def connect_and_reconnect_loop():
            """Try to connect and keep retrying on failure.
            This is for reconnections after initial setup or if disconnect_callback is triggered.
            """
            while hass.state is not CoreState.stopping:
                try:
                    transport, protocol = await try_connect_once()
                    _LOGGER.info("Successfully (re)connected to Rflink.")
                    async_dispatcher_send(hass, SIGNAL_AVAILABILITY, True)
                    RflinkCommand.set_rflink_protocol(protocol, wait_for_ack)
                    
                    # Ensure transport is closed on HA stop.
                    # Manage listener to avoid duplicates if loop runs multiple times.
                    # One way is to store transport and have a single stop listener.
                    # For simplicity, assuming create_rflink_connection handles this or
                    # this is managed carefully.
                    # A simple approach for the stop listener:
                    listener_unsubscribe = hass.bus.async_listen_once(
                        EVENT_HOMEASSISTANT_STOP, lambda x: transport.close()
                    )
                    # Wait until disconnect_callback (schedule_reconnect_on_disconnect) is called
                    # or HA stops. This requires a mechanism for schedule_reconnect_on_disconnect
                    # to signal this loop to retry. The rflink library's disconnect_callback
                    # will trigger a new call to this loop. So, this loop instance can exit here.
                    return
                except (SerialException, OSError, TimeoutError) as ex:
                    _LOGGER.warning(
                        "Failed to connect to Rflink: %s. Retrying in %s seconds",
                        ex,
                        reconnect_interval,
                    )
                except Exception as ex:  # pylint: disable=broad-except
                    _LOGGER.exception(
                        "Unhandled error during Rflink connection attempt: %s. Retrying in %s seconds",
                        ex, reconnect_interval
                    )
                
                RflinkCommand.set_rflink_protocol(None) # Ensure protocol is cleared
                async_dispatcher_send(hass, SIGNAL_AVAILABILITY, False)
                if hass.state is not CoreState.stopping:
                    await asyncio.sleep(reconnect_interval)


        # --- Initial connection attempt for async_setup ---
        try:
            transport, protocol = await try_connect_once()
            _LOGGER.info("Successfully connected to Rflink on initial setup.")
            async_dispatcher_send(hass, SIGNAL_AVAILABILITY, True)
            RflinkCommand.set_rflink_protocol(protocol, wait_for_ack)
            # Listen for Home Assistant stop event to close transport
            hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STOP, lambda x: transport.close()
            )
        except (SerialException, OSError, TimeoutError) as ex:
            _LOGGER.error(
                "Error connecting to Rflink during initial setup: %s. "
                "Integration will not be loaded. Please check configuration and device.",
                ex
            )
            # Do not schedule reconnect here; setup has failed.
            return False  # CRUCIAL: Signal Home Assistant that setup failed
        except Exception as ex:  # pylint: disable=broad-except
             _LOGGER.exception("Unhandled error during Rflink initial setup: %s.", ex)
             return False # Signal Home Assistant that setup failed

        # If initial connection is successful, normal setup continues.
        # The disconnect_callback (schedule_reconnect_on_disconnect) handles future disconnections
        # by calling connect_and_reconnect_loop.

        async_dispatcher_connect(hass, SIGNAL_EVENT, event_callback)

        # ... (setup for handle_logging_changed) ...
        # async def handle_logging_changed(_: Event) -> None: ...
        # hass.bus.async_listen(EVENT_LOGGING_CHANGED, handle_logging_changed)

        return True
    ```

    **Explanation of Changes:**
    *   `async_setup` now directly calls and awaits `try_connect_once()`.
    *   If `try_connect_once()` fails (raises `SerialException`, `OSError`, `TimeoutError`, or any other exception during connection), `async_setup` catches this, logs an error, and returns `False`. This fulfills the rule's requirement.
    *   The `schedule_reconnect_on_disconnect` function is passed as the `disconnect_callback` to `create_rflink_connection`. This callback is invoked by the `rflink` library if the connection drops *after* it was successfully established. It then initiates the `connect_and_reconnect_loop`.
    *   The `connect_and_reconnect_loop` is responsible for persistently trying to reconnect in the background if the connection is lost after the initial setup or if triggered by the disconnect callback.

    This refactoring ensures that Home Assistant is immediately aware if the `rflink` integration cannot connect during its initial setup phase. The persistent reconnection logic is preserved for maintaining the connection or re-establishing it after a temporary outage, but only after a successful initial load.

_Created at 2025-05-28 13:34:08. Prompt tokens: 17793, Output tokens: 2478, Total tokens: 26378_
