# Home Assistant Quality Scale checker

Home Assistant is made up of thousands of integrations. Official integration quality rules have been created to help maintain an overall great level of quality among these integrations. Integrations that pass these rules can grow their quality ranking to bronze, silver, gold and finally platinum. These rules are [extensively documented](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/) and define the perfect user experience, documentation, error handling and performance for integrations.

This repository contains a collection of scripts to use AI to generate reports if an integration follows a rule, and if not, what it should do to improve. [Generated reports can be found here.](https://github.com/balloob/home-assistant-quality-checker/tree/main/generated)

_Disclaimer: AI can be wrong, and following guidance from these reports will not guarantee that your contribution will be accepted into Home Assistant._

## Generating your own report

The scrips use the Google Gemini API. Create a file `.token` that contains your Google Gemini API key. You can [create one here.](https://aistudio.google.com/apikey).

### checker.py

This script will test an integration against the Home Assistant integration quality scale rules. It will generate a report for each rule.

```bash
uv run checker.py wled
```

#### --core-path

By default it assumes that the Home Assistant core repository exists as `../core`. If that is not the case, specify it by adding `--core-path` to the command line.

#### --integration-path

Specify the direct path to the integration's directory. If this is provided, the script will load the integration from this path. The positional `domain` argument becomes optional, and if not provided, will be inferred from the directory name. Example: `uv run checker.py --integration-path /path/to/my_integration`

#### --target-scale

By default it will stop checking rules for the first integration quality scale level that has rules left to be done. Set `--target-scale silver` to check all rules for the silver level and below.

#### --free

The configured model is set to a paid model and requires billing to be enabled. Add `--free` to the command line to use a free model. Quality will be lower.

#### --single-rule

Only run a single rule. This is useful for testing and debugging.

#### --force-update

By default it will not generate reports that are already generated. Set `--force-update` to force the generation of reports.

#### --dry-run

Set `--dry-run` to only print the rules that would be checked, without actually checking them. This is useful for testing and debugging.

#### --include-done

Set `--include-done` to generate reports for rules that are already marked done.

### fixer.py

This script will take a generated report and use it to fix the issues in the integration by generating a diff.

```bash
uv run fixer.py wled has-entity-name
```

#### --core-path

By default it assumes that the Home Assistant core repository exists as `../core`. If that is not the case, specify it by adding `--core-path` to the command line.
