# home_connect: unique-config-entry

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [unique-config-entry](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/unique-config-entry)                                                     |
| Status | **done**                                                                 |

## Overview

The `unique-config-entry` rule requires that an integration must not allow the same device or service to be set up twice. This is to prevent duplicated devices and entities, and potential unique identifier collisions. The rule applies to the `home_connect` integration as it involves setting up a connection to the Home Connect cloud service via a UI-based configuration flow (OAuth2).

The `home_connect` integration correctly follows this rule by implementing the "Unique identifier" method described in the rule documentation.

In `config_flow.py`, the `OAuth2FlowHandler` class's `async_oauth_create_entry` method is responsible for creating the configuration entry:

```python
# home_connect/config_flow.py
    async def async_oauth_create_entry(self, data: dict) -> ConfigFlowResult:
        """Create an oauth config entry or update existing entry for reauth."""
        await self.async_set_unique_id(  # [1]
            jwt.decode(
                data["token"]["access_token"], options={"verify_signature": False}
            )["sub"]  # [2]
        )
        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="wrong_account")
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data_updates=data
            )
        self._abort_if_unique_id_configured()  # [3]
        return await super().async_oauth_create_entry(data)
```

**Explanation:**

1.  `await self.async_set_unique_id(...)`: The integration sets a unique ID for the configuration entry.
2.  The unique ID is derived from the `sub` (subject) claim of the OAuth2 access token. The `sub` claim is a standard OpenID Connect claim that provides a unique identifier for the end-user at the issuer. This ensures that each distinct Home Connect account will have a unique identifier.
3.  `self._abort_if_unique_id_configured()`: After setting the unique ID, this method is called. It checks if a configuration entry with this `unique_id` already exists for the `home_connect` domain. If an entry with the same `unique_id` (i.e., the same Home Connect account) is already configured, the current configuration flow is aborted, preventing a duplicate setup.

This mechanism effectively ensures that the same Home Connect account cannot be configured multiple times. If a user attempts to re-authenticate (e.g., due to an expired token), the reauth flow also uses this unique ID to ensure it's updating the correct existing entry and handles mismatches if the user tries to reauth with a different account.

Additionally, the migration logic in `__init__.py` (version 1, minor_version 3) ensures that older config entries are updated to use this `sub` claim as their `unique_id`, further solidifying the uniqueness across integration updates:
```python
# home_connect/__init__.py
            case 2: # (referring to minor_version)
                hass.config_entries.async_update_entry(
                    entry,
                    minor_version=3,
                    unique_id=jwt.decode(
                        entry.data["token"]["access_token"],
                        options={"verify_signature": False},
                    )["sub"],
                )
```

Therefore, the `home_connect` integration correctly implements measures to prevent duplicate configuration entries for the same service account.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 20:32:13. Prompt tokens: 141671, Output tokens: 908, Total tokens: 145375_
