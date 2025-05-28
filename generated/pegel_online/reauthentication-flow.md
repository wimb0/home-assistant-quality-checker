```markdown
# pegel_online: reauthentication-flow

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [pegel_online](https://www.home-assistant.io/integrations/pegel_online/) |
| Rule   | [reauthentication-flow](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow)                                                     |
| Status | **exempt**                                       |
| Reason | The integration does not require any form of authentication or credentials that could expire or change. |

## Overview

This rule requires integrations that use authentication or credentials (like API keys, passwords) to provide a UI flow for users to reauthenticate if their credentials become invalid.

Upon reviewing the `pegel_online` integration code, specifically the `config_flow.py`, `__init__.py`, and `coordinator.py` files, it's evident that the integration connects to the PEGELONLINE API using the `aiopegelonline` library without requiring any form of user authentication or API key.

The `ConfigFlow` in `homeassistant/components/pegel_online/config_flow.py` only prompts for location and radius to find stations, and then allows selecting a station UUID. There are no fields or steps related to entering or managing credentials.

The API calls made by the `aiopegelonline` library within `__init__.py` (`async_get_station_details`) and `coordinator.py` (`async_get_station_measurements`) do not involve passing any authentication tokens or credentials. The caught `CONNECT_ERRORS` are related to network connectivity or API availability, not authentication failures.

Since the integration interacts with a public API endpoint that does not require user authentication, there is no scenario where user credentials would expire or change, triggering a need for reauthentication. Therefore, the `reauthentication-flow` rule does not apply to this integration.

```

_Created at 2025-05-25 11:23:56. Prompt tokens: 6415, Output tokens: 429, Total tokens: 7347_
