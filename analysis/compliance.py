import yaml
from pathlib import Path
from .client import ClaudeClient

PROMPTS_PATH = Path(__file__).parent.parent / "config" / "prompts.yaml"
PROFILE_PATH = Path(__file__).parent.parent / "config" / "company_profile.yaml"


def analyze_compliance(client: ClaudeClient, document_text: str, company_profile: str | None = None) -> list:
    prompts = yaml.safe_load(PROMPTS_PATH.read_text())

    if company_profile is None:
        company_profile = PROFILE_PATH.read_text()

    system = prompts["compliance"]["system"]
    user = (
        prompts["compliance"]["user"]
        .replace("{document_text}", document_text)
        .replace("{company_profile}", company_profile)
    )
    result = client.analyze(system, user)
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "_raw_response" not in result:
        for key in result:
            if isinstance(result[key], list):
                return result[key]
    return result
