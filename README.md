# Home Assistant Quality Scale checker

Check the quality scale of a Home Assistant integration.

# Usage

Create a file `.token` that contains your Google Gemini API key. You can [create one here.](https://aistudio.google.com/apikey)

```bash
uv run checker.py wled
```

By default it assumes that the Home Assistant core repository exists as `../core`. If that is not the case, specify it by adding `--core-path` to the command line.
