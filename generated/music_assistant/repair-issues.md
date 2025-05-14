# music_assistant: repair-issues

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [music_assistant](https://www.home-assistant.io/integrations/music_assistant/) |
| Rule   | [repair-issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues)                                                     |
| Status | **done**                                                                 |
| Reason | (Only include if Status is "exempt". Explain why the rule does not apply.) |

## Overview

The `repair-issues` rule states that repair issues and repair flows should be used when user intervention is needed, and these issues should be actionable and informative. Integrations should not raise repair issues for problems the user cannot fix themselves.

This rule applies to the `music_assistant` integration as it connects to an external Music Assistant server, and situations may arise (like server version incompatibility) where user intervention is required to resolve an issue.

The `music_assistant` integration correctly follows this rule by implementing a repair issue for the `InvalidServerVersion` scenario.

Specifically, in `homeassistant/components/music_assistant/__init__.py`:
```python
# lines 57-73
    try:
        async with asyncio.timeout(CONNECT_TIMEOUT):
            await mass.connect()
    except (TimeoutError, CannotConnect) as err:
        raise ConfigEntryNotReady(
            f"Failed to connect to music assistant server {mass_url}"
        ) from err
    except InvalidServerVersion as err: # <-- This is the relevant part
        async_create_issue(
            hass,
            DOMAIN,
            "invalid_server_version",
            is_fixable=False,
            severity=IssueSeverity.ERROR,
            translation_key="invalid_server_version",
        )
        raise ConfigEntryNotReady(f"Invalid server version: {err}") from err
    # ...
    async_delete_issue(hass, DOMAIN, "invalid_server_version") # Issue is cleared if resolved
```

This implementation adheres to the rule's requirements:
1.  **User Intervention Needed:** An `InvalidServerVersion` error means the Music Assistant server version is incompatible with the integration. The user needs to intervene by updating their Music Assistant server.
2.  **Actionable and Informative:** The `translation_key="invalid_server_version"` points to strings defined in `homeassistant/components/music_assistant/strings.json` (and its translations, e.g., `translations/en.json`):
    ```json
    "issues": {
      "invalid_server_version": {
        "title": "The Music Assistant server is not the correct version",
        "description": "Check if there are updates available for the Music Assistant server and/or integration."
      }
    }
    ```
    This message clearly informs the user of the problem and suggests an actionable step (checking for updates).
3.  **User Can Fix:** The user can resolve this issue by updating their Music Assistant server software.
4.  **`is_fixable=False`:** This is appropriate because Home Assistant cannot automatically fix an external server's version. The rule's own example also uses `is_fixable=False` for a similar scenario.
5.  **Issue Deletion:** The issue is correctly deleted using `async_delete_issue` if the connection is successful on a subsequent attempt, indicating the version issue might have been resolved.
6.  **Raising `ConfigEntryNotReady`:** After creating the issue, `ConfigEntryNotReady` is raised, which is consistent with the pattern shown in the rule's example (which uses `ConfigEntryError`, a subclass of `ConfigEntryNotReady`). This prevents the integration from loading in a broken state.

The integration demonstrates correct usage of the repair issue system for a relevant problem, aligning with the rule's intent and example.

## Suggestions

No suggestions needed.

_Created at 2025-05-14 13:46:08. Prompt tokens: 30074, Output tokens: 882, Total tokens: 35228_
