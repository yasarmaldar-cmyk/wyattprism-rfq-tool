import yaml
from pathlib import Path
from .client import ClaudeClient

PROMPTS_PATH = Path(__file__).parent.parent / "config" / "prompts.yaml"


def analyze_checklist(client: ClaudeClient, document_text: str) -> dict:
    prompts = yaml.safe_load(PROMPTS_PATH.read_text())
    system = prompts["checklist"]["system"]
    user = prompts["checklist"]["user"].replace("{document_text}", document_text)
    return client.analyze(system, user)
