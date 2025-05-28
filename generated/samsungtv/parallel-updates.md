```markdown
# samsungtv: parallel-updates

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/)       |
| Rule   | [parallel-updates](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates) |
| Status | **done**                                                                 |

## Overview

This rule requires that integrations explicitly set `PARALLEL_UPDATES` in their entity platform files. This is done to control the number of simultaneous requests sent to a device or service, which is particularly important for devices sensitive to being overloaded.

The `samsungtv` integration utilizes a data update coordinator (`SamsungTVDataUpdateCoordinator`) defined in `coordinator.py`. The rule specifies that when a coordinator is used, `PARALLEL_UPDATES` should typically be set to `0` for read-only platforms, and can also be set to `0` for platforms with actions if the coordinator handles the main update logic.

The `samsungtv` integration includes the `media_player.py` and `remote.py` platforms. Both files correctly define `PARALLEL_UPDATES = 0` at the top level, which aligns with the recommended practice when using a data update coordinator:

*   `homeassistant/components/samsungtv/media_player.py` includes `PARALLEL_UPDATES = 0` on line 61.
*   `homeassistant/components/samsungtv/remote.py` includes `PARALLEL_UPDATES = 0` on line 17.

This configuration indicates that the coordinator is responsible for handling the update rate, and the entity platforms themselves do not initiate parallel updates that need limitation via this constant. The actions performed by the media player and remote entities (like sending keys via the bridge) are handled individually or through the coordinator's refresh logic, and the core framework's parallel update mechanism controlled by `PARALLEL_UPDATES` isn't necessary to limit concurrency *between* entities of the same platform when set to 0.

Therefore, the integration correctly follows the `parallel-updates` rule by explicitly setting the constant with the appropriate value given its architecture.

## Suggestions

No suggestions needed.
```

_Created at 2025-05-25 11:30:37. Prompt tokens: 30094, Output tokens: 510, Total tokens: 31233_
