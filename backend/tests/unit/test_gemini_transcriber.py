import httpx
import pytest
import respx

from vetscribe_backend.transcription.gemini_transcriber import GeminiTranscriber


@respx.mock
def test_transcribe_sends_base64_audio_and_returns_text():
    route = respx.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": "patient is a 5 year old lab"}]}}
                ]
            },
        )
    )

    transcriber = GeminiTranscriber(api_key="key123", model="gemini-2.0-flash")
    text = transcriber.transcribe(b"RIFF....fake-wav-bytes....")

    assert text == "patient is a 5 year old lab"
    request = route.calls.last.request
    assert request.url.params["key"] == "key123"


@respx.mock
def test_transcribe_raises_on_http_error():
    respx.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    ).mock(return_value=httpx.Response(403, json={"error": "invalid key"}))

    transcriber = GeminiTranscriber(api_key="bad-key", model="gemini-2.0-flash")

    with pytest.raises(httpx.HTTPStatusError):
        transcriber.transcribe(b"RIFF....")
