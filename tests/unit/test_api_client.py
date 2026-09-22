import json

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
def test_generate_soap_note_parses_transcript_from_response():
    respx.post("https://vetscribe.example.com/api/soap").mock(
        return_value=httpx.Response(
            200,
            json={
                "subjective": "sub",
                "objective": "obj",
                "assessment": "assess",
                "plan": "plan",
                "transcript": "The owner reports the dog has been vomiting since yesterday.",
            },
        )
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=30)
    note = client.generate_soap_note(b"RIFF....")

    assert note.transcript == "The owner reports the dog has been vomiting since yesterday."


@respx.mock
def test_generate_soap_note_defaults_transcript_to_empty_when_absent():
    # Older backends respond without a transcript field; the client must not
    # crash and should surface an empty transcript rather than raising.
    respx.post("https://vetscribe.example.com/api/soap").mock(
        return_value=httpx.Response(
            200,
            json={
                "subjective": "sub",
                "objective": "obj",
                "assessment": "assess",
                "plan": "plan",
            },
        )
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=30)
    note = client.generate_soap_note(b"RIFF....")

    assert note.transcript == ""


@respx.mock
def test_generate_soap_note_raises_api_client_error_on_timeout():
    respx.post("https://vetscribe.example.com/api/soap").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError, match="timed out"):
        client.generate_soap_note(b"RIFF....")


@respx.mock
def test_generate_soap_note_raises_api_client_error_on_connection_refused():
    respx.post("https://vetscribe.example.com/api/soap").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError, match="connection refused"):
        client.generate_soap_note(b"RIFF....")


@respx.mock
def test_generate_soap_note_raises_api_client_error_on_http_error_status():
    respx.post("https://vetscribe.example.com/api/soap").mock(
        return_value=httpx.Response(500, json={"error": "internal server error"})
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError, match="500"):
        client.generate_soap_note(b"RIFF....")


@respx.mock
def test_generate_soap_note_sends_authorization_header_when_api_key_configured():
    route = respx.post("https://vetscribe.example.com/api/soap").mock(
        return_value=httpx.Response(
            200,
            json={
                "subjective": "sub",
                "objective": "obj",
                "assessment": "assess",
                "plan": "plan",
            },
        )
    )

    client = ApiClient(
        endpoint="https://vetscribe.example.com/api/soap",
        timeout_seconds=30,
        api_key="secret-token",
    )
    client.generate_soap_note(b"RIFF....")

    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer secret-token"


@respx.mock
def test_generate_soap_note_omits_authorization_header_when_no_api_key():
    route = respx.post("https://vetscribe.example.com/api/soap").mock(
        return_value=httpx.Response(
            200,
            json={
                "subjective": "sub",
                "objective": "obj",
                "assessment": "assess",
                "plan": "plan",
            },
        )
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=30)
    client.generate_soap_note(b"RIFF....")

    request = route.calls.last.request
    assert "Authorization" not in request.headers


@respx.mock
def test_generate_soap_note_raises_api_client_error_on_malformed_json():
    respx.post("https://vetscribe.example.com/api/soap").mock(
        return_value=httpx.Response(200, json={"subjective": "only one field present"})
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError, match="objective"):
        client.generate_soap_note(b"RIFF....")


@respx.mock
def test_regenerate_soap_note_posts_transcript_json_to_regenerate_endpoint():
    route = respx.post("https://vetscribe.example.com/api/soap/regenerate").mock(
        return_value=httpx.Response(
            200,
            json={
                "subjective": "Owner reports limping.",
                "objective": "Left forelimb lameness.",
                "assessment": "Soft-tissue strain.",
                "plan": "Rest and NSAIDs, recheck in 2 weeks.",
                "transcript": "the owner says the dog is limping",
            },
        )
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=30)
    note = client.regenerate_soap_note("the owner says the dog is limping")

    assert route.called
    request = route.calls.last.request
    assert json.loads(request.content) == {
        "transcript": "the owner says the dog is limping"
    }
    assert note.subjective == "Owner reports limping."
    assert note.transcript == "the owner says the dog is limping"


@respx.mock
def test_regenerate_soap_note_derives_endpoint_when_base_has_trailing_slash():
    route = respx.post("https://vetscribe.example.com/api/soap/regenerate").mock(
        return_value=httpx.Response(
            200,
            json={
                "subjective": "s",
                "objective": "o",
                "assessment": "a",
                "plan": "p",
            },
        )
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap/", timeout_seconds=5)
    client.regenerate_soap_note("some transcript")

    assert route.called


@respx.mock
def test_regenerate_soap_note_sends_authorization_header_when_api_key_configured():
    route = respx.post("https://vetscribe.example.com/api/soap/regenerate").mock(
        return_value=httpx.Response(
            200,
            json={"subjective": "s", "objective": "o", "assessment": "a", "plan": "p"},
        )
    )

    client = ApiClient(
        endpoint="https://vetscribe.example.com/api/soap",
        timeout_seconds=5,
        api_key="secret-token",
    )
    client.regenerate_soap_note("transcript")

    assert route.calls.last.request.headers["Authorization"] == "Bearer secret-token"


@respx.mock
def test_regenerate_soap_note_raises_api_client_error_on_connection_refused():
    respx.post("https://vetscribe.example.com/api/soap/regenerate").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError):
        client.regenerate_soap_note("transcript")


@respx.mock
def test_regenerate_soap_note_raises_api_client_error_on_http_error_status():
    respx.post("https://vetscribe.example.com/api/soap/regenerate").mock(
        return_value=httpx.Response(502, json={"error": "upstream provider error"})
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError, match="502"):
        client.regenerate_soap_note("transcript")


@respx.mock
def test_fetch_pending_injections_returns_requests_list():
    route = respx.get("https://vetscribe.example.com/api/injections/pending").mock(
        return_value=httpx.Response(
            200,
            json={
                "requests": [
                    {
                        "id": "req-1",
                        "exam_id": "exam-1",
                        "created_at": "2026-09-22T00:00:00+00:00",
                        "status": "pending",
                        "outcome": None,
                        "exam": {
                            "id": "exam-1",
                            "subjective": "s",
                            "objective": "o",
                            "assessment": "a",
                            "plan": "p",
                            "transcript": "t",
                        },
                    }
                ]
            },
        )
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)
    requests = client.fetch_pending_injections()

    assert route.called
    assert len(requests) == 1
    assert requests[0]["id"] == "req-1"
    assert requests[0]["exam"]["assessment"] == "a"


@respx.mock
def test_fetch_pending_injections_sends_bearer_token_when_configured():
    route = respx.get("https://vetscribe.example.com/api/injections/pending").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )

    client = ApiClient(
        endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5, api_key="secret"
    )
    assert client.fetch_pending_injections() == []
    assert route.calls.last.request.headers["Authorization"] == "Bearer secret"


@respx.mock
def test_fetch_pending_injections_raises_api_client_error_on_transport_failure():
    respx.get("https://vetscribe.example.com/api/injections/pending").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError):
        client.fetch_pending_injections()


@respx.mock
def test_fetch_pending_injections_raises_on_http_error_status():
    respx.get("https://vetscribe.example.com/api/injections/pending").mock(
        return_value=httpx.Response(500, text="boom")
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError, match="500"):
        client.fetch_pending_injections()


@respx.mock
def test_ack_injection_posts_outcome_to_the_request_endpoint():
    route = respx.post("https://vetscribe.example.com/api/injections/req-1/ack").mock(
        return_value=httpx.Response(200, json={"id": "req-1", "status": "done"})
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)
    client.ack_injection("req-1", outcome="injected")

    assert route.called
    assert json.loads(route.calls.last.request.content) == {"outcome": "injected"}


@respx.mock
def test_ack_injection_raises_api_client_error_on_transport_failure():
    respx.post("https://vetscribe.example.com/api/injections/req-1/ack").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    client = ApiClient(endpoint="https://vetscribe.example.com/api/soap", timeout_seconds=5)

    with pytest.raises(ApiClientError):
        client.ack_injection("req-1", outcome="injected")
