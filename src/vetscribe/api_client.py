import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("vetscribe.api_client")


class ApiClientError(Exception):
    pass


@dataclass
class SoapNote:
    subjective: str
    objective: str
    assessment: str
    plan: str


class ApiClient:
    def __init__(self, endpoint: str, timeout_seconds: float, api_key: str = ""):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key

    def generate_soap_note(self, audio_bytes: bytes) -> SoapNote:
        headers = {"Content-Type": "audio/wav"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        logger.info("POST %s (timeout=%ss)", self.endpoint, self.timeout_seconds)
        try:
            response = httpx.post(
                self.endpoint,
                content=audio_bytes,
                headers=headers,
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            logger.error("backend request timed out: %s", exc)
            raise ApiClientError(f"request timed out: {exc}") from exc

        logger.info("backend responded with status %s", response.status_code)
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
