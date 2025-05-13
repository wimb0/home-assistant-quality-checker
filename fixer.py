# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "google-genai==1.7.0",
#     "pyyaml",
#     "requests",
# ]
# ///
"""Address issues raised by a rule report."""

import datetime
import logging
import json
import ast
import sys
import yaml
from pathlib import Path

from google import genai
import requests


from checker import QUALITY_SCALE_RULE_RAW_URL, get_integration_files_for_prompt

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "generated"


GENERATE_PATCH_PROMPT = """
You are an expert Home Assistant Python code assistant. Your primary function is to generate code patches based on quality rule violations.

**Objective:**
Generate a patch file to address specific issues found in the Home Assistant integration "{integration}". These issues are violations of the quality scale rule {rule}.

**Instructions:**
1.  Analyze the provided **Rule Definition** and the **Violation Report**.
2.  Identify the exact changes needed in the **Integration Code Files** to comply with the rule and resolve the reported issues.
3.  Generate a patch reflecting these changes.
4.  The patch **MUST** be in the **unified diff format** (e.g., the output of `diff -u old_file new_file`).
5.  The patch should **ONLY** contain the necessary code modifications. Do **NOT** include any explanatory text, comments, or conversational filler before or after the diff block. Your entire output should be the raw diff.
6.  Focus on making the minimum necessary changes to achieve compliance.
7.  If multiple files are provided, ensure the diff correctly indicates changes for each respective file.

**Input Details:**

**1. The integration:**
{integration}

**2. The Rule Name/ID:**
{rule}

--- START OF ATTACHED FILES ---

--- FILE: rule-{rule}-description.md ---
{rule_content}
--- END FILE ---

--- FILE: rule-{rule}-report.md ---
{report_content}
--- END FILE ---

{files}

--- END OF ATTACHED FILES ---
""".strip()


def get_args() -> tuple:
    """
    Get command line arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Check quality scale for an integration."
    )
    parser.add_argument(
        "integration",
        help="The integration to check.",
        type=str,
    )
    parser.add_argument(
        "rule",
        help="The rule whose report has to be addressed.",
        type=str,
    )
    parser.add_argument(
        "--core-path",
        help="Path to Home Assistant core.",
        type=str,
        default="../core",
    )
    return parser.parse_args()


def main(token: str, args) -> None:
    """
    Main function to run the script.
    """
    core_path = Path(args.core_path).resolve()

    if not core_path.is_dir():
        logger.error(f"Core path {core_path} does not exist.")
        sys.exit(1)

    integration_path = core_path / "homeassistant" / "components" / args.integration

    if not integration_path.is_dir():
        logger.error(f"Integration path {integration_path} does not exist.")
        sys.exit(1)

    report_path = OUTPUT_DIR / args.integration / f"{args.rule}.md"

    if not report_path.is_file():
        logger.error(f"Report path {report_path} does not exist.")
        sys.exit(1)

    integration_files = get_integration_files_for_prompt(integration_path)
    client = genai.Client(api_key=token)

    response = client.models.generate_content(
        model="gemini-2.5-pro-exp-03-25",
        contents=GENERATE_PATCH_PROMPT.format(
            integration=args.integration,
            rule=args.rule,
            rule_content=requests.get(
                QUALITY_SCALE_RULE_RAW_URL.format(args.rule)
            ).text,
            report_content=report_path.read_text(encoding="utf-8"),
            files=integration_files,
        ),
    )

    diff_path = OUTPUT_DIR / args.integration / f"{args.rule}.diff"

    diff_path.write_text(
        response.text,
        encoding="utf-8",
    )
    print(f"Diff file written to {diff_path}")
    print(
        "Prompt tokens: {prompt_tokens}, Output tokens: {output_tokens}, Total tokens: {total_tokens}".format(
            datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            prompt_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.candidates_token_count,
            total_tokens=response.usage_metadata.total_token_count,
        )
    )


if __name__ == "__main__":
    token_path = Path(".token")
    if not token_path.exists():
        print("No token file found. Please create a .token file with your API key.")
        sys.exit(1)
    token = token_path.read_text(encoding="utf-8").strip()
    main(token, get_args())
