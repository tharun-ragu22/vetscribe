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
        try:
            response = httpx.post(
                self.endpoint,
                content=audio_bytes,
                headers={"Content-Type": "audio/wav"},
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise ApiClientError(f"request timed out: {exc}") from exc

        if response.status_code != 200:
            raise ApiClientError(f"backend returned {response.status_code}: {response.text}")

        data = response.json()
        try:
            return SoapNote(
                subjective=data["subjective"],
                objective=data["objective"],
                assessment=data["assessment"],
                plan=data["plan"],
            )
        except KeyError as exc:
            raise ApiClientError(f"backend response missing field: {exc}") from exc
