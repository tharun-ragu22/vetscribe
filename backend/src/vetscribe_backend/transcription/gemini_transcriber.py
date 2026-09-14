import base64

import httpx

ENDPOINT_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class TranscriptionError(Exception):
    pass


class GeminiTranscriber:
    def __init__(self, api_key: str, model: str, timeout_seconds: float = 60):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def transcribe(self, audio_bytes: bytes) -> str:
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        response = httpx.post(
            ENDPOINT_TEMPLATE.format(model=self.model),
            params={"key": self.api_key},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": "Transcribe this audio verbatim. Respond with only the transcript text."},
                            {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}},
                        ]
                    }
                ]
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as exc:
            block_reason = data.get("promptFeedback", {}).get("blockReason")
            finish_reason = (data.get("candidates") or [{}])[0].get("finishReason")
            raise TranscriptionError(
                "Gemini returned no transcribable content "
                f"(blockReason={block_reason}, finishReason={finish_reason}); "
                "the audio may be empty, silent, or blocked"
            ) from exc
