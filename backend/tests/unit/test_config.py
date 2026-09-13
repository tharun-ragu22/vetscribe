from vetscribe_backend.config import BackendConfig


def test_from_env_reads_provider_selection_and_keys(monkeypatch):
    monkeypatch.setenv("VETSCRIBE_TRANSCRIPTION_PROVIDER", "gemini")
    monkeypatch.setenv("VETSCRIBE_NOTE_PROVIDER", "anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic")
    monkeypatch.setenv("GEMINI_API_KEY", "sk-gemini")
    monkeypatch.setenv("VETSCRIBE_BACKEND_API_KEY", "shared-secret")

    config = BackendConfig.from_env()

    assert config.transcription_provider == "gemini"
    assert config.note_provider == "anthropic"
    assert config.openai_api_key == "sk-openai"
    assert config.anthropic_api_key == "sk-anthropic"
    assert config.gemini_api_key == "sk-gemini"
    assert config.backend_api_key == "shared-secret"


def test_from_env_defaults_to_openai_for_both_providers(monkeypatch):
    monkeypatch.delenv("VETSCRIBE_TRANSCRIPTION_PROVIDER", raising=False)
    monkeypatch.delenv("VETSCRIBE_NOTE_PROVIDER", raising=False)

    config = BackendConfig.from_env()

    assert config.transcription_provider == "openai"
    assert config.note_provider == "openai"


def test_from_env_defaults_backend_api_key_to_empty_string(monkeypatch):
    monkeypatch.delenv("VETSCRIBE_BACKEND_API_KEY", raising=False)

    config = BackendConfig.from_env()

    assert config.backend_api_key == ""
