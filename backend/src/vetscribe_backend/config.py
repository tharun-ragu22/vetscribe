import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_DEFAULT_DOTENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@dataclass
class BackendConfig:
    transcription_provider: str
    note_provider: str
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openai_transcription_model: str = "whisper-1"
    openai_note_model: str = "gpt-4o-mini"
    anthropic_note_model: str = "claude-sonnet-4-5"
    gemini_transcription_model: str = "gemini-2.0-flash"
    gemini_note_model: str = "gemini-2.0-flash"
    backend_api_key: str = ""

    @classmethod
    def from_env(cls, dotenv_path: Path | str | None = None) -> "BackendConfig":
        load_dotenv(dotenv_path or _DEFAULT_DOTENV_PATH)
        return cls(
            transcription_provider=os.environ.get("VETSCRIBE_TRANSCRIPTION_PROVIDER", "openai"),
            note_provider=os.environ.get("VETSCRIBE_NOTE_PROVIDER", "openai"),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
            openai_transcription_model=os.environ.get("OPENAI_TRANSCRIPTION_MODEL", "whisper-1"),
            openai_note_model=os.environ.get("OPENAI_NOTE_MODEL", "gpt-4o-mini"),
            anthropic_note_model=os.environ.get("ANTHROPIC_NOTE_MODEL", "claude-sonnet-4-5"),
            gemini_transcription_model=os.environ.get(
                "GEMINI_TRANSCRIPTION_MODEL", "gemini-2.0-flash"
            ),
            gemini_note_model=os.environ.get("GEMINI_NOTE_MODEL", "gemini-2.0-flash"),
            backend_api_key=os.environ.get("VETSCRIBE_BACKEND_API_KEY", ""),
        )
