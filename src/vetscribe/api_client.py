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
    transcript: str = ""


class ApiClient:
    def __init__(self, endpoint: str, timeout_seconds: float, api_key: str = ""):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key

    def _auth_headers(self, extra: dict) -> dict:
        headers = dict(extra)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _parse_soap_response(self, response) -> SoapNote:
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
                transcript=data.get("transcript", ""),
            )
        except KeyError as exc:
            raise ApiClientError(f"backend response missing field: {exc}") from exc

    def generate_soap_note(self, audio_bytes: bytes) -> SoapNote:
        headers = self._auth_headers({"Content-Type": "audio/wav"})

        logger.info("POST %s (timeout=%ss)", self.endpoint, self.timeout_seconds)
        try:
            response = httpx.post(
                self.endpoint,
                content=audio_bytes,
                headers=headers,
                timeout=self.timeout_seconds,
            )
        except httpx.RequestError as exc:
            logger.error("backend request failed: %s", exc)
            raise ApiClientError(f"request failed: {exc}") from exc

        return self._parse_soap_response(response)

    def _api_base(self) -> str:
        # The configured endpoint is the audio POST URL (".../api/soap"); the
        # injection endpoints live alongside it under ".../api/injections", so
        # drop the trailing path segment. Keeps a single configured URL.
        return self.endpoint.rstrip("/").rsplit("/", 1)[0]

    def fetch_pending_injections(self) -> list:
        # Poll the backend for mobile-originated requests to paste a note into
        # AVImark. Each request carries the exam's current note to inject.
        url = f"{self._api_base()}/injections/pending"
        headers = self._auth_headers({})
        try:
            response = httpx.get(url, headers=headers, timeout=self.timeout_seconds)
        except httpx.RequestError as exc:
            logger.error("fetch pending injections failed: %s", exc)
            raise ApiClientError(f"request failed: {exc}") from exc

        if response.status_code != 200:
            raise ApiClientError(
                f"backend returned {response.status_code}: {response.text}"
            )
        return response.json().get("requests", [])

    def ack_injection(self, request_id: str, outcome: str) -> None:
        # Tell the backend a pending injection request has been handled so it's
        # dropped from the pending list and never re-delivered.
        url = f"{self._api_base()}/injections/{request_id}/ack"
        headers = self._auth_headers({"Content-Type": "application/json"})
        try:
            response = httpx.post(
                url, json={"outcome": outcome}, headers=headers, timeout=self.timeout_seconds
            )
        except httpx.RequestError as exc:
            logger.error("ack injection failed: %s", exc)
            raise ApiClientError(f"request failed: {exc}") from exc

        if response.status_code != 200:
            raise ApiClientError(
                f"backend returned {response.status_code}: {response.text}"
            )

    def regenerate_soap_note(self, transcript: str) -> SoapNote:
        # Ask the backend to re-run only note generation over a hand-corrected
        # transcript. Derived from the same base endpoint the audio POST uses so
        # only one URL needs configuring.
        url = self.endpoint.rstrip("/") + "/regenerate"
        headers = self._auth_headers({"Content-Type": "application/json"})

        logger.info("POST %s (timeout=%ss)", url, self.timeout_seconds)
        try:
            response = httpx.post(
                url,
                json={"transcript": transcript},
                headers=headers,
                timeout=self.timeout_seconds,
            )
        except httpx.RequestError as exc:
            logger.error("backend regenerate request failed: %s", exc)
            raise ApiClientError(f"request failed: {exc}") from exc

        return self._parse_soap_response(response)
