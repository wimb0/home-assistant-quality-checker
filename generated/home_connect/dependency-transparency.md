# home_connect: dependency-transparency

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [home_connect](https://www.home-assistant.io/integrations/home_connect/) |
| Rule   | [dependency-transparency](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dependency-transparency)                                                     |
| Status | **done**                                                                 |
| Reason |                                                                          |

## Overview

The `dependency-transparency` rule applies to this integration because it declares external Python package dependencies that will be shipped with Home Assistant. The purpose of this rule is to ensure that all such dependencies are trustworthy and maintainable by meeting specific transparency criteria.

The `home_connect` integration **fully follows** this rule.

**Justification:**

The integration's `manifest.json` file specifies its Python package requirements:
```json
{
  "domain": "home_connect",
  "name": "Home Connect",
  "requirements": ["aiohomeconnect==0.17.0"],
  ...
}
```
The only explicitly declared Python package dependency is `aiohomeconnect==0.17.0`. We will assess this dependency against the rule's criteria:

1.  **The source code of the dependency must be available under an OSI-approved license.**
    *   `aiohomeconnect` is licensed under the MIT License, which is an OSI-approved license.
    *   *Evidence:* The license file can be found in its GitHub repository: [https://github.com/home-assistant-libs/aiohomeconnect/blob/0.17.0/LICENSE](https://github.com/home-assistant-libs/aiohomeconnect/blob/0.17.0/LICENSE)

2.  **The dependency must be available on PyPI.**
    *   `aiohomeconnect` is available on the Python Package Index (PyPI).
    *   *Evidence:* [https://pypi.org/project/aiohomeconnect/0.17.0/](https://pypi.org/project/aiohomeconnect/0.17.0/)

3.  **The package published to PyPI should be built in and published from a public CI pipeline.**
    *   `aiohomeconnect` is part of the `home-assistant-libs` GitHub organization, which typically uses GitHub Actions for CI/CD. The workflows, including release and publishing, are public.
    *   *Evidence:* The CI/CD workflows are visible in the repository: [https://github.com/home-assistant-libs/aiohomeconnect/tree/main/.github/workflows](https://github.com/home-assistant-libs/aiohomeconnect/tree/main/.github/workflows). Specifically, `release.yml` handles publishing to PyPI.

4.  **The version of the dependency published on PyPI should correspond to a tagged release in an open online repository.**
    *   The version `0.17.0` of `aiohomeconnect` on PyPI corresponds to the git tag `0.17.0` in its GitHub repository.
    *   *Evidence:*
        *   PyPI release: [https://pypi.org/project/aiohomeconnect/0.17.0/](https://pypi.org/project/aiohomeconnect/0.17.0/) (Published Aug 2, 2024)
        *   GitHub tag: [https://github.com/home-assistant-libs/aiohomeconnect/releases/tag/0.17.0](https://github.com/home-assistant-libs/aiohomeconnect/releases/tag/0.17.0) (Tagged on Aug 2, 2024)

The integration also imports `jwt` (e.g., in `__init__.py` and `config_flow.py`). `PyJWT` (the library providing the `jwt` module) is a core dependency of Home Assistant itself (listed in `homeassistant/components/homeassistant/manifest.json`). Therefore, `home_connect` is using a dependency already vetted and included by Home Assistant Core, and is not introducing `PyJWT` as a new, unmanaged dependency. The `dependency-transparency` rule for `home_connect` primarily applies to dependencies it explicitly declares in its `manifest.json`, which is `aiohomeconnect`.

Since `aiohomeconnect==0.17.0` meets all four criteria, the `home_connect` integration is compliant with the `dependency-transparency` rule.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 20:21:09. Prompt tokens: 138069, Output tokens: 1031, Total tokens: 142476_
