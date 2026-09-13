import httpx

from vetscribe_backend.note_generation.parsing import parse_soap_json
from vetscribe_backend.prompts import SOAP_SYSTEM_PROMPT
from vetscribe_backend.schemas import SoapNote


class AnthropicNoteGenerator:
    ENDPOINT = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 60):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, transcript: str) -> SoapNote:
        response = httpx.post(
            self.ENDPOINT,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": self.ANTHROPIC_VERSION,
            },
            json={
                "model": self.model,
                "max_tokens": 1024,
                "system": SOAP_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": transcript}],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        content = response.json()["content"][0]["text"]
        return parse_soap_json(content)
