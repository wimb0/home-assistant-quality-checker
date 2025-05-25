```markdown
# fritzbox: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry) |
| Status | **done**                                                                 |

## Overview

This rule requires that an integration prevents the user from setting up the same device or service more than once via the user interface. This is essential to avoid duplicate devices and potential unique identifier conflicts.

The `fritzbox` integration is a hub integration connecting to a single FRITZ!Box router to manage its smart home devices. The rule is applicable as a user could attempt to set up the same router multiple times.

The integration implements checks in its `config_flow.py` file to prevent duplicate config entries for the same FRITZ!Box:

1.  **User Initiated Flow (`async_step_user`):** When the user manually enters the host information, the flow calls `self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})`. This checks if an existing configuration entry already exists with the same host specified by the user. If a match is found, the flow aborts with the `already_configured` reason, preventing a duplicate entry based on the hostname/IP address.
2.  **Discovery Flow (`async_step_ssdp`):** When the FRITZ!Box is discovered via SSDP, the integration extracts the host from the discovery info. If a UPnP UDN (Unique Device Name), which often contains a UUID, is found, it sets the unique ID for the flow using `await self.async_set_unique_id(uuid)`. It then uses `self._abort_if_unique_id_configured({CONF_HOST: host})`. While the unique ID is set, this method also checks for existing entries that match the provided data (`{CONF_HOST: host}`), effectively preventing duplicates based on both the discovered UUID (if available) and the host. Additionally, the code explicitly iterates through existing entries to update the unique_id if a match is found based only on the host, ensuring older entries get the UUID identifier, and then aborts if the host is already configured. The flow also implements `is_matching` based on the host to prevent multiple discovery flows for the same device running concurrently.

These checks correctly implement the requirement to ensure that only one configuration entry can exist for a given FRITZ!Box router, satisfying the `unique-config-entry` rule.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:21:11. Prompt tokens: 19617, Output tokens: 600, Total tokens: 21576_
