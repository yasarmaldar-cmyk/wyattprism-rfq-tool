import json
import yaml
from pathlib import Path
from .client import ClaudeClient

PROMPTS_PATH = Path(__file__).parent.parent / "config" / "prompts.yaml"


def generate_proposal(
    client: ClaudeClient,
    document_text: str,
    summary: dict,
    answered_clarifications: list[dict] | None = None,
) -> str:
    """Generate a proposal draft based on the RFQ, its summary, and any answered clarifications."""
    prompts = yaml.safe_load(PROMPTS_PATH.read_text())
    system = prompts["proposal"]["system"]

    summary_json = json.dumps(summary, indent=2, default=str)

    user = (
        prompts["proposal"]["user"]
        .replace("{summary_json}", summary_json)
        .replace("{document_text}", document_text)
    )

    # Append answered clarifications as extra context
    if answered_clarifications:
        answers_block = "\n\nCLARIFICATION ANSWERS FROM THE BD TEAM:\n"
        answers_block += "Use these answers to make the proposal MORE SPECIFIC and ACCURATE.\n\n"
        for i, item in enumerate(answered_clarifications, 1):
            answers_block += f"Q{i} [{item.get('category', 'general').upper()}]: {item['question']}\n"
            answers_block += f"A{i}: {item['answer']}\n\n"
        answers_block += (
            "IMPORTANT: Incorporate these answers into the scope of work, timeline, "
            "and any other relevant sections. If an answer specifies a framework, "
            "include framework-specific deliverables. If an answer clarifies page counts "
            "or specs, use those exact numbers."
        )
        user += answers_block

    # Use higher max_tokens for proposal
    result = client.analyze(system, user, max_tokens=8192)

    # The proposal should be raw text, not JSON
    if isinstance(result, dict) and result.get("_raw_response"):
        return result["_raw_response"]
    if isinstance(result, dict) and result.get("_parse_error"):
        return result.get("_raw_response", "")
    if isinstance(result, dict):
        return json.dumps(result, indent=2)
    return str(result)
