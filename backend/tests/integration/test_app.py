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
        self.received_transcript = None

    def process(self, audio_bytes):
        self.received_audio = audio_bytes
        if self.error is not None:
            raise self.error
        return self.result

    def generate_from_transcript(self, transcript):
        self.received_transcript = transcript
        if self.error is not None:
            raise self.error
        # Echo the caller's transcript back, mirroring the real pipeline.
        return SoapResult(note=self.result.note, transcript=transcript)


def test_create_soap_note_returns_200_with_note_and_transcript_json(make_config):
    note = SoapNote(subjective="s", objective="o", assessment="a", plan="p")
    pipeline = FakePipeline(note=note, transcript="owner reports vomiting")
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post(
        "/api/soap", content=b"RIFF....audio....", headers={"Content-Type": "audio/wav"}
    )

    assert response.status_code == 200
    body = response.json()
    # The note is now persisted, so the response also carries an id + timestamp.
    assert body["subjective"] == "s"
    assert body["objective"] == "o"
    assert body["assessment"] == "a"
    assert body["plan"] == "p"
    assert body["transcript"] == "owner reports vomiting"
    assert body["id"]
    assert body["created_at"]
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


def test_regenerate_returns_200_with_note_from_transcript(make_config):
    note = SoapNote(subjective="s", objective="o", assessment="a", plan="p")
    pipeline = FakePipeline(note=note)
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post(
        "/api/soap/regenerate", json={"transcript": "the corrected transcript"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "subjective": "s",
        "objective": "o",
        "assessment": "a",
        "plan": "p",
        "transcript": "the corrected transcript",
    }
    assert pipeline.received_transcript == "the corrected transcript"


def test_regenerate_returns_400_on_missing_transcript(make_config):
    pipeline = FakePipeline(note=SoapNote(subjective="s", objective="o", assessment="a", plan="p"))
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post("/api/soap/regenerate", json={})

    assert response.status_code == 400
    assert pipeline.received_transcript is None


def test_regenerate_returns_400_on_blank_transcript(make_config):
    pipeline = FakePipeline(note=SoapNote(subjective="s", objective="o", assessment="a", plan="p"))
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post("/api/soap/regenerate", json={"transcript": "   "})

    assert response.status_code == 400


def test_regenerate_requires_bearer_token_when_backend_api_key_configured(make_config):
    pipeline = FakePipeline(note=SoapNote(subjective="s", objective="o", assessment="a", plan="p"))
    app = create_app(config=make_config(backend_api_key="secret"), pipeline=pipeline)
    client = TestClient(app)

    response = client.post("/api/soap/regenerate", json={"transcript": "t"})

    assert response.status_code == 401


def test_regenerate_returns_502_when_note_generation_fails(make_config):
    pipeline = FakePipeline(
        note=SoapNote(subjective="s", objective="o", assessment="a", plan="p"),
        error=httpx.ConnectError("connection refused"),
    )
    app = create_app(config=make_config(), pipeline=pipeline)
    client = TestClient(app)

    response = client.post("/api/soap/regenerate", json={"transcript": "t"})

    assert response.status_code == 502


# --- Cross-device sync: history + exam editing ------------------------------

from vetscribe_backend.store import ExamStore  # noqa: E402


def _note(a="a"):
    return SoapNote(subjective="s", objective="o", assessment=a, plan="p")


def test_create_soap_note_persists_exam_so_it_appears_in_history(make_config):
    note = SoapNote(subjective="s", objective="o", assessment="a", plan="p")
    pipeline = FakePipeline(note=note, transcript="owner reports vomiting")
    store = ExamStore()
    app = create_app(config=make_config(), pipeline=pipeline, store=store)
    client = TestClient(app)

    posted = client.post("/api/soap", content=b"RIFF....").json()
    history = client.get("/api/history").json()

    assert [e["id"] for e in history["exams"]] == [posted["id"]]
    assert history["exams"][0]["transcript"] == "owner reports vomiting"


def test_history_returns_exams_newest_first(make_config):
    store = ExamStore()
    first = store.add(_note("first"), transcript="t1")
    second = store.add(_note("second"), transcript="t2")
    app = create_app(config=make_config(), pipeline=FakePipeline(note=_note()), store=store)
    client = TestClient(app)

    exams = client.get("/api/history").json()["exams"]

    assert [e["id"] for e in exams] == [second.id, first.id]


def test_history_requires_bearer_token_when_backend_api_key_configured(make_config):
    app = create_app(
        config=make_config(backend_api_key="secret"),
        pipeline=FakePipeline(note=_note()),
        store=ExamStore(),
    )
    client = TestClient(app)

    assert client.get("/api/history").status_code == 401
    ok = client.get("/api/history", headers={"Authorization": "Bearer secret"})
    assert ok.status_code == 200


def test_get_exam_returns_the_exam_and_404_when_unknown(make_config):
    store = ExamStore()
    exam = store.add(_note(), transcript="t")
    app = create_app(config=make_config(), pipeline=FakePipeline(note=_note()), store=store)
    client = TestClient(app)

    found = client.get(f"/api/exams/{exam.id}")
    assert found.status_code == 200
    assert found.json()["id"] == exam.id

    assert client.get("/api/exams/nope").status_code == 404


def test_update_exam_saves_edits_and_returns_the_updated_exam(make_config):
    store = ExamStore()
    exam = store.add(_note(), transcript="original")
    app = create_app(config=make_config(), pipeline=FakePipeline(note=_note()), store=store)
    client = TestClient(app)

    response = client.put(
        f"/api/exams/{exam.id}",
        json={
            "subjective": "s2",
            "objective": "o2",
            "assessment": "a2",
            "plan": "p2",
            "transcript": "corrected",
        },
    )

    assert response.status_code == 200
    assert response.json()["assessment"] == "a2"
    assert response.json()["transcript"] == "corrected"
    # id + created_at are preserved
    assert response.json()["id"] == exam.id
    assert response.json()["created_at"] == exam.created_at
    assert store.get(exam.id).transcript == "corrected"


def test_update_exam_returns_404_for_unknown_id(make_config):
    app = create_app(config=make_config(), pipeline=FakePipeline(note=_note()), store=ExamStore())
    client = TestClient(app)

    response = client.put(
        "/api/exams/missing",
        json={"subjective": "", "objective": "", "assessment": "", "plan": "", "transcript": ""},
    )

    assert response.status_code == 404


def test_update_exam_returns_400_when_required_fields_missing(make_config):
    store = ExamStore()
    exam = store.add(_note(), transcript="t")
    app = create_app(config=make_config(), pipeline=FakePipeline(note=_note()), store=store)
    client = TestClient(app)

    response = client.put(f"/api/exams/{exam.id}", json={"subjective": "only"})

    assert response.status_code == 400


def test_update_exam_requires_bearer_token_when_backend_api_key_configured(make_config):
    store = ExamStore()
    exam = store.add(_note(), transcript="t")
    app = create_app(
        config=make_config(backend_api_key="secret"),
        pipeline=FakePipeline(note=_note()),
        store=store,
    )
    client = TestClient(app)

    response = client.put(
        f"/api/exams/{exam.id}",
        json={"subjective": "s", "objective": "o", "assessment": "a", "plan": "p", "transcript": "t"},
    )

    assert response.status_code == 401
