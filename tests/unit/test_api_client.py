import httpx
import pytest
import respx

from vetscribe.api_client import ApiClient, ApiClientError


@respx.mock
def test_generate_soap_note_posts_audio_bytes_and_returns_parsed_note():
    route = respx.post("https://vetscribe.example.com/api/soap").mock(
        return_value=httpx.Response(
            200,
            json={
                "subjective": "Patient presented for annual checkup.",
                "objective": "Temp 101.5F, HR 120bpm.",
                "assessment": "Healthy adult canine.",
                "plan": "Continue current diet, recheck in 1 year.",
            },
        )
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=30)
    note = client.generate_soap_note(b"RIFF....fake-wav-bytes....")

    assert route.called
    request = route.calls.last.request
    assert request.content == b"RIFF....fake-wav-bytes...."
    assert note.subjective == "Patient presented for annual checkup."
    assert note.objective == "Temp 101.5F, HR 120bpm."
    assert note.assessment == "Healthy adult canine."
    assert note.plan == "Continue current diet, recheck in 1 year."


@respx.mock
def test_generate_soap_note_raises_api_client_error_on_timeout():
    respx.post("https://vetscribe.example.com/api/soap").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError, match="timed out"):
        client.generate_soap_note(b"RIFF....")


@respx.mock
def test_generate_soap_note_raises_api_client_error_on_http_error_status():
    respx.post("https://vetscribe.example.com/api/soap").mock(
        return_value=httpx.Response(500, json={"error": "internal server error"})
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError, match="500"):
        client.generate_soap_note(b"RIFF....")
