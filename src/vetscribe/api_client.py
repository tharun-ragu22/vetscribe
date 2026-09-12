from dataclasses import dataclass

import httpx


class ApiClientError(Exception):
    pass


@dataclass
class SoapNote:
    subjective: str
    objective: str
    assessment: str
    plan: str


class ApiClient:
    def __init__(self, endpoint: str, timeout_seconds: float):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def generate_soap_note(self, audio_bytes: bytes) -> SoapNote:
        response = httpx.post(
            self.endpoint,
            content=audio_bytes,
            headers={"Content-Type": "audio/wav"},
            timeout=self.timeout_seconds,
        )
        data = response.json()
        return SoapNote(
            subjective=data["subjective"],
            objective=data["objective"],
            assessment=data["assessment"],
            plan=data["plan"],
        )
