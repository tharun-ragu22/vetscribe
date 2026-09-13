from abc import ABC, abstractmethod

from vetscribe_backend.config import BackendConfig


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str: ...


class UnknownProviderError(Exception):
    pass


def get_transcriber(config: BackendConfig) -> Transcriber:
    from vetscribe_backend.transcription.gemini_transcriber import GeminiTranscriber
    from vetscribe_backend.transcription.openai_transcriber import OpenAiTranscriber

    if config.transcription_provider == "openai":
        return OpenAiTranscriber(
            api_key=config.openai_api_key, model=config.openai_transcription_model
        )
    if config.transcription_provider == "gemini":
        return GeminiTranscriber(
            api_key=config.gemini_api_key, model=config.gemini_transcription_model
        )
    raise UnknownProviderError(f"unknown transcription provider: {config.transcription_provider}")
