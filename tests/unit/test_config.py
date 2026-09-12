from vetscribe.config import Config, DEFAULT_CONFIG


def test_config_returns_defaults_when_no_file_exists(tmp_path):
    config_path = tmp_path / "config.json"

    config = Config.load(config_path)

    assert config.api_endpoint == DEFAULT_CONFIG["api_endpoint"]
    assert config.api_timeout_seconds == DEFAULT_CONFIG["api_timeout_seconds"]
    assert config.hotkey == DEFAULT_CONFIG["hotkey"]
