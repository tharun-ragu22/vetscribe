from abc import ABC, abstractmethod

from vetscribe_backend.config import BackendConfig
from vetscribe_backend.schemas import SoapNote


class NoteGenerator(ABC):
    provider_name: str

    @classmethod
    @abstractmethod
    def from_config(cls, config: BackendConfig) -> "NoteGenerator": ...

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

    providers: dict[str, type[NoteGenerator]] = {
        cls.provider_name: cls
        for cls in (OpenAiNoteGenerator, AnthropicNoteGenerator, GeminiNoteGenerator)
    }
    try:
        generator_cls = providers[config.note_provider]
    except KeyError:
        raise UnknownProviderError(f"unknown note provider: {config.note_provider}") from None
    return generator_cls.from_config(config)
