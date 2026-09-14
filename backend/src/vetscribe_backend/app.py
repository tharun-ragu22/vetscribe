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

    @app.post("/api/soap")
    async def create_soap_note(request: Request):
        if config.backend_api_key:
            expected = f"Bearer {config.backend_api_key}"
            if request.headers.get("authorization") != expected:
                return JSONResponse({"error": "unauthorized"}, status_code=401)

        audio_bytes = await request.body()
        if not audio_bytes:
            return JSONResponse({"error": "empty request body"}, status_code=400)

        try:
            soap_note = pipeline.process(audio_bytes)
        except httpx.HTTPStatusError as exc:
            return JSONResponse({"error": f"upstream provider error: {exc}"}, status_code=502)
        except httpx.RequestError as exc:
            return JSONResponse({"error": f"upstream request failed: {exc}"}, status_code=502)
        except (NoteParsingError, TranscriptionError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=502)

        return JSONResponse(soap_note.to_dict())

    return app
