import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from vetscribe_backend.config import BackendConfig
from vetscribe_backend.note_generation import get_note_generator
from vetscribe_backend.note_generation.parsing import NoteParsingError
from vetscribe_backend.pipeline import SoapPipeline
from vetscribe_backend.transcription import get_transcriber
from vetscribe_backend.transcription.gemini_transcriber import TranscriptionError


def create_app(config: BackendConfig | None = None, pipeline: SoapPipeline | None = None) -> FastAPI:
    config = config or BackendConfig.from_env()
    pipeline = pipeline or SoapPipeline(
        transcriber=get_transcriber(config),
        note_generator=get_note_generator(config),
    )

    app = FastAPI()

    def _unauthorized(request: Request) -> JSONResponse | None:
        if not config.backend_api_key:
            return None
        expected = f"Bearer {config.backend_api_key}"
        if request.headers.get("authorization") != expected:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return None

    def _provider_error_response(exc: Exception) -> JSONResponse:
        # Map every provider-level failure to a clean 502 rather than a raw 500
        # traceback. New provider failure modes belong in this tuple.
        if isinstance(exc, httpx.HTTPStatusError):
            return JSONResponse({"error": f"upstream provider error: {exc}"}, status_code=502)
        if isinstance(exc, httpx.RequestError):
            return JSONResponse({"error": f"upstream request failed: {exc}"}, status_code=502)
        return JSONResponse({"error": str(exc)}, status_code=502)

    _PROVIDER_ERRORS = (
        httpx.HTTPStatusError,
        httpx.RequestError,
        NoteParsingError,
        TranscriptionError,
    )

    @app.post("/api/soap")
    async def create_soap_note(request: Request):
        unauthorized = _unauthorized(request)
        if unauthorized is not None:
            return unauthorized

        audio_bytes = await request.body()
        if not audio_bytes:
            return JSONResponse({"error": "empty request body"}, status_code=400)

        try:
            result = pipeline.process(audio_bytes)
        except _PROVIDER_ERRORS as exc:
            return _provider_error_response(exc)

        return JSONResponse(result.to_dict())

    @app.post("/api/soap/regenerate")
    async def regenerate_soap_note(request: Request):
        # Re-run note generation from a (hand-corrected) transcript, no audio.
        unauthorized = _unauthorized(request)
        if unauthorized is not None:
            return unauthorized

        try:
            body = await request.json()
        except ValueError:
            return JSONResponse({"error": "invalid JSON body"}, status_code=400)
        transcript = (body or {}).get("transcript", "")
        if not isinstance(transcript, str) or not transcript.strip():
            return JSONResponse({"error": "missing transcript"}, status_code=400)

        try:
            result = pipeline.generate_from_transcript(transcript)
        except _PROVIDER_ERRORS as exc:
            return _provider_error_response(exc)

        return JSONResponse(result.to_dict())

    return app
