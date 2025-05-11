# wled: dependency-transparency

| Info   | Value                                                                    |
|--------|--------------------------------------------------------------------------|
| Name   | [wled](https://www.home-assistant.io/integrations/wled/) |
| Rule   | [dependency-transparency](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dependency-transparency)                                                     |
| Status | **done**                                       |
| Reason |                                                                          |

## Overview

The `dependency-transparency` rule applies to this integration as it defines external dependencies. The rule requires that these dependencies meet specific criteria for trustworthiness and openness:
1.  The source code of the dependency must be available under an OSI-approved license.
2.  The dependency must be available on PyPI.
3.  The package published to PyPI should be built in and published from a public CI pipeline.
4.  The version of the dependency published on PyPI should correspond to a tagged release in an open online repository.

The `wled` integration declares one dependency in its `manifest.json` file:
```json
{
  "domain": "wled",
  "name": "WLED",
  "codeowners": ["@frenck"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/wled",
  "integration_type": "device",
  "iot_class": "local_push",
  "requirements": ["wled==0.21.0"],
  "zeroconf": ["_wled._tcp.local."]
}
```
The dependency is `wled==0.21.0`. Let's check this dependency against the rule's criteria:

1.  **Source Code and OSI-approved License:**
    *   The source code for the `python-wled` library is hosted on GitHub: [https://github.com/frenck/python-wled](https://github.com/frenck/python-wled).
    *   The repository contains a `LICENSE` file ([https://github.com/frenck/python-wled/blob/v0.21.0/LICENSE](https://github.com/frenck/python-wled/blob/v0.21.0/LICENSE)) which specifies the MIT License.
    *   The MIT License is an OSI-approved license. This criterion is met.

2.  **Availability on PyPI:**
    *   The `wled` package is available on PyPI: [https://pypi.org/project/wled/0.21.0/](https://pypi.org/project/wled/0.21.0/). This criterion is met.

3.  **Public CI for PyPI Publication:**
    *   The `python-wled` GitHub repository uses GitHub Actions for its CI/CD.
    *   The workflow file for publishing to PyPI can be found at [`.github/workflows/publish.yaml`](https://github.com/frenck/python-wled/blob/main/.github/workflows/publish.yaml).
    *   This workflow is triggered on the creation of new tags and uses the `pypa/gh-action-pypi-publish` action to publish the package to PyPI. GitHub Actions is a public CI service. This criterion is met.

4.  **PyPI Version Corresponds to Tagged Release:**
    *   The version specified in `manifest.json` is `0.21.0`.
    *   The `python-wled` GitHub repository has a corresponding tagged release `v0.21.0`: [https://github.com/frenck/python-wled/releases/tag/v0.21.0](https://github.com/frenck/python-wled/releases/tag/v0.21.0). This criterion is met.

Since all dependencies listed in the `manifest.json` (in this case, only `wled==0.21.0`) meet all the requirements of the `dependency-transparency` rule, the integration is considered compliant.

## Suggestions

No suggestions needed.

_Created at 2025-05-10 19:26:32. Prompt tokens: 20212, Output tokens: 949, Total tokens: 21903_
