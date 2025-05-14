# Home Assistant Quality Scale checker

Check the quality scale of a Home Assistant integration.

The scrips use the Google Gemini API. Create a file `.token` that contains your Google Gemini API key. You can [create one here.](https://aistudio.google.com/apikey).

# checker.py

This script will test an integration against the Home Assistant integration quality scale rules. It will generate a report for each rule.

```bash
uv run checker.py wled
```

## --core-path

By default it assumes that the Home Assistant core repository exists as `../core`. If that is not the case, specify it by adding `--core-path` to the command line.

## --target-scale

By default it will stop checking rules for the first integration quality scale level that has rules left to be done. Set `--target-scale silver` to check all rules for the silver level and below.

## --free

The configured model is set to a paid model and requires billing to be enabled. Add `--free` to the command line to use a free model. Quality will be lower.

## --force-update

By default it will not generate reports that are already generated. Set `--force-update` to force the generation of reports.

## --dry-run

Set `--dry-run` to only print the rules that would be checked, without actually checking them. This is useful for testing and debugging.

## --include-done

Set `--include-done` to generate reports for rules that are already marked done.

# fixer.py

This script will take a generated report and use it to fix the issues in the integration by generating a diff.

```bash
uv run fixer.py wled has-entity-name
```

## --core-path

By default it assumes that the Home Assistant core repository exists as `../core`. If that is not the case, specify it by adding `--core-path` to the command line.
