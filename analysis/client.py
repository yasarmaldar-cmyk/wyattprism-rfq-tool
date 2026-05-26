import json
import re
import anthropic
from dotenv import load_dotenv

load_dotenv()


class ClaudeClient:
    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str | None = None):
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = anthropic.Anthropic()
        self.model = model
        self.last_usage = None

    def analyze(self, system_prompt: str, user_prompt: str, max_tokens: int = 8192) -> dict:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        self.last_usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        raw_text = response.content[0].text
        return self._parse_json(raw_text)

    def _parse_json(self, text: str) -> dict:
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Return raw text wrapped in a dict as fallback
        return {"_raw_response": text, "_parse_error": True}
