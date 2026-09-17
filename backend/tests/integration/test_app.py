import httpx
from fastapi.testclient import TestClient

from vetscribe_backend.app import create_app
from vetscribe_backend.schemas import SoapNote, SoapResult
from vetscribe_backend.transcription.gemini_transcriber import TranscriptionError


class FakePipeline:
    def __init__(self, note=None, transcript="", error=None):
        self.result = SoapResult(note=note, transcript=transcript) if note is not None else None
        self.error = error
        self.received_audio = None

    def process(self, audio_bytes):
        self.received_audio = audio_bytes
        if self.error is not None:
            raise self.error
        return self.result


def test_create_soap_note_returns_200_with_note_and_transcript_json(make_config):
    note = SoapNote(subjective="s", objective="o", assessment="a", plan="p")
    pipeline = FakePipeline(note=note, transcript="owner reports vomiting")
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post(
        "/api/soap", content=b"RIFF....audio....", headers={"Content-Type": "audio/wav"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "subjective": "s",
        "objective": "o",
        "assessment": "a",
        "plan": "p",
        "transcript": "owner reports vomiting",
    }
    assert pipeline.received_audio == b"RIFF....audio...."


def test_create_soap_note_rejects_missing_bearer_token_when_backend_api_key_configured(
    make_config,
):
    pipeline = FakePipeline(note=SoapNote(subjective="s", objective="o", assessment="a", plan="p"))
    app = create_app(config=make_config(backend_api_key="secret"), pipeline=pipeline)
    client = TestClient(app)

    response = client.post("/api/soap", content=b"RIFF....")

    assert response.status_code == 401


def test_create_soap_note_rejects_wrong_bearer_token(make_config):
    pipeline = FakePipeline(note=SoapNote(subjective="s", objective="o", assessment="a", plan="p"))
    app = create_app(config=make_config(backend_api_key="secret"), pipeline=pipeline)
    client = TestClient(app)

    response = client.post(
        "/api/soap", content=b"RIFF....", headers={"Authorization": "Bearer wrong-token"}
    )

    assert response.status_code == 401


def test_create_soap_note_accepts_correct_bearer_token(make_config):
    note = SoapNote(subjective="s", objective="o", assessment="a", plan="p")
    pipeline = FakePipeline(note=note)
    app = create_app(config=make_config(backend_api_key="secret"), pipeline=pipeline)
    client = TestClient(app)

    response = client.post(
        "/api/soap", content=b"RIFF....", headers={"Authorization": "Bearer secret"}
    )

    assert response.status_code == 200


def test_create_soap_note_returns_502_when_upstream_provider_unreachable(make_config):
    pipeline = FakePipeline(error=httpx.ConnectError("connection refused"))
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post("/api/soap", content=b"RIFF....")

    assert response.status_code == 502


def test_create_soap_note_returns_502_when_upstream_returns_error_status(make_config):
    pipeline = FakePipeline(
        error=httpx.HTTPStatusError(
            "bad request", request=httpx.Request("POST", "https://example.com"),
            response=httpx.Response(400, request=httpx.Request("POST", "https://example.com")),
        )
    )
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post("/api/soap", content=b"RIFF....")

    assert response.status_code == 502


def test_create_soap_note_returns_502_when_transcription_yields_no_content(make_config):
    pipeline = FakePipeline(error=TranscriptionError("Gemini returned no transcribable content"))
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post("/api/soap", content=b"RIFF....")

    assert response.status_code == 502


def test_create_soap_note_returns_400_on_empty_body(make_config):
    pipeline = FakePipeline(note=None)
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post("/api/soap", content=b"")

    assert response.status_code == 400
    assert pipeline.received_audio is None
