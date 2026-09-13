from abc import ABC, abstractmethod

from vetscribe_backend.config import BackendConfig
from vetscribe_backend.schemas import SoapNote


class NoteGenerator(ABC):
    @abstractmethod
    def generate(self, transcript: str) -> SoapNote: ...


class UnknownProviderError(Exception):
    pass


def get_note_generator(config: BackendConfig) -> NoteGenerator:
    from vetscribe_backend.note_generation.anthropic_note_generator import (
        AnthropicNoteGenerator,
    )
    from vetscribe_backend.note_generation.gemini_note_generator import GeminiNoteGenerator
    from vetscribe_backend.note_generation.openai_note_generator import OpenAiNoteGenerator

    if config.note_provider == "openai":
        return OpenAiNoteGenerator(api_key=config.openai_api_key, model=config.openai_note_model)
    if config.note_provider == "anthropic":
        return AnthropicNoteGenerator(
            api_key=config.anthropic_api_key, model=config.anthropic_note_model
        )
    if config.note_provider == "gemini":
        return GeminiNoteGenerator(api_key=config.gemini_api_key, model=config.gemini_note_model)
    raise UnknownProviderError(f"unknown note provider: {config.note_provider}")
