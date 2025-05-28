```markdown
# samsungtv: action-setup

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [samsungtv](https://www.home-assistant.io/integrations/samsungtv/) |
| Rule   | [action-setup](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup)                                                     |
| Status | **done**                                                                 |

## Overview

The `action-setup` rule requires integrations to register any custom service actions within the `async_setup` function rather than `async_setup_entry`. This allows Home Assistant to validate automation configurations involving these services even if the specific configuration entry for the service is not currently loaded.

Upon reviewing the `samsungtv` integration code, specifically in `homeassistant/components/samsungtv/__init__.py`, it is apparent that the integration does not define or register any custom services using `hass.services.async_register`. The integration relies on the standard services provided by the `media_player` and `remote` platforms for the entities it creates (as seen in `media_player.py` and `remote.py`).

Since no custom services are registered at all, there are no services being incorrectly registered in `async_setup_entry`. The integration inherently complies with the requirement of the `action-setup` rule by not having any custom services to register in the first place. The `async_setup` function in `__init__.py` is present but only contains the line `return True`, confirming that no custom service registration occurs there either.

Therefore, the integration fully follows the requirements of this rule.
```

_Created at 2025-05-25 11:27:40. Prompt tokens: 30251, Output tokens: 366, Total tokens: 31724_
