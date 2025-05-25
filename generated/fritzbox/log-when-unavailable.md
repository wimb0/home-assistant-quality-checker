```markdown
# fritzbox: log-when-unavailable

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [fritzbox](https://www.home-assistant.io/integrations/fritzbox/)         |
| Rule   | [log-when-unavailable](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable) |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

This rule requires that an integration logs when its connection to a device or service becomes unavailable and again when it becomes available, logging only once for each state change to avoid log spam. The `fritzbox` integration connects to a FRITZ!Box router and polls its devices, making this rule applicable.

The integration uses a `DataUpdateCoordinator` (`FritzboxDataUpdateCoordinator` in `coordinator.py`) to manage fetching data from the FRITZ!Box. The `_async_update_data` method within the coordinator is responsible for performing the update logic.

Looking at the `_async_update_data` method and the helper `_update_fritz_devices` it calls in `homeassistant/components/fritzbox/coordinator.py`, we see that connection issues are handled:

```python
    def _update_fritz_devices(self) -> FritzboxCoordinatorData:
        """Update all fritzbox device data."""
        try:
            self.fritz.update_devices(ignore_removed=False)
            if self.has_templates:
                self.fritz.update_templates(ignore_removed=False)
        except RequestConnectionError as ex:
            raise UpdateFailed from ex
        except HTTPError:
            # If the device rebooted, login again
            try:
                self.fritz.login()
            except LoginError as ex:
                raise ConfigEntryAuthFailed from ex
            self.fritz.update_devices(ignore_removed=False)
            if self.has_templates:
                self.fritz.update_templates(ignore_removed=False)
```

The `RequestConnectionError` exception, which indicates a connection failure, is caught and re-raised as an `UpdateFailed` exception. Similarly, certain `HTTPError` scenarios might lead to a re-login attempt, and failure during that or the subsequent update could also result in exceptions caught by the outer `_async_update_data` (or the `LoginError` raising `ConfigEntryAuthFailed`).

When a `DataUpdateCoordinator` encounters an `UpdateFailed` exception during its update cycle, the Home Assistant core automatically logs this failure at the `ERROR` level. Furthermore, the coordinator base class also includes logic to log an `INFO` message when polling is successful again after a failure. This built-in behavior of the `DataUpdateCoordinator` satisfies the requirements of the `log-when-unavailable` rule: it logs once when the update fails (signaling unavailability) and once when a subsequent update succeeds (signaling it's back online), thereby avoiding log spam.

Although the rule's example for coordinators shows an `info` log for the unavailable state, the standard practice for errors caught by the coordinator leading to `UpdateFailed` is `ERROR`, which is appropriate for indicating a problem. The core coordinator logic handles the recovery logging at `INFO`. The implementation aligns with the rule's intent by utilizing the standard coordinator pattern.

Therefore, the `fritzbox` integration correctly follows the `log-when-unavailable` rule by leveraging the built-in logging capabilities of the `DataUpdateCoordinator`.

## Suggestions

No suggestions needed. The integration correctly implements the pattern for coordinator-based integrations.
```

_Created at 2025-05-25 11:34:51. Prompt tokens: 19282, Output tokens: 818, Total tokens: 21619_
