import json
import yaml
from pathlib import Path
from .client import ClaudeClient

PROMPTS_PATH = Path(__file__).parent.parent / "config" / "prompts.yaml"


def analyze_clarifications(client: ClaudeClient, document_text: str, summary_context: dict = None) -> list:
    prompts = yaml.safe_load(PROMPTS_PATH.read_text())
    system = prompts["clarifications"]["system"]

    # Build enhanced user prompt with summary context
    user_template = prompts["clarifications"]["user"]
    user = user_template.replace("{document_text}", document_text)

    # Inject summary context so clarifications are informed by detected industry/frameworks
    if summary_context and not summary_context.get("_parse_error"):
        org = summary_context.get("issuing_organization", {})
        frameworks = summary_context.get("frameworks", {})
        report_type = summary_context.get("report_type", "Unknown")

        context_block = f"""
ANALYSIS CONTEXT (from prior summary):
- Organization: {org.get('name', 'Unknown')} ({org.get('type', 'Unknown')})
- Sector: {org.get('sector', 'Unknown')}
- Report Type: {report_type}
- Frameworks Detected: {', '.join(frameworks.get('detected', [])) or 'NONE'}
- Frameworks Implied: {', '.join(frameworks.get('implied', [])) or 'NONE'}
- No Framework Mentioned: {frameworks.get('no_framework_detected', False)}

Use this context to generate SMARTER, MORE SPECIFIC clarification questions.
If no framework is detected, you MUST recommend specific frameworks based on the organization's
sector and report type, and generate questions about framework adoption.
"""
        user = context_block + "\n" + user

    result = client.analyze(system, user, max_tokens=8192)

    # Handle various response formats
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "_raw_response" not in result:
        for key in result:
            if isinstance(result[key], list):
                return result[key]
    return result
