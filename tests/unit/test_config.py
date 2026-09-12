import json

from vetscribe.config import Config, DEFAULT_CONFIG


def test_config_returns_defaults_when_no_file_exists(tmp_path):
    config_path = tmp_path / "config.json"

    config = Config.load(config_path)

    assert config.api_endpoint == DEFAULT_CONFIG["api_endpoint"]
    assert config.api_timeout_seconds == DEFAULT_CONFIG["api_timeout_seconds"]
    assert config.hotkey == DEFAULT_CONFIG["hotkey"]


def test_config_loads_values_from_existing_file(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "api_endpoint": "https://vetscribe.example.com/api/soap",
        "api_timeout_seconds": 45,
        "hotkey": "<ctrl>+<alt>+v",
    }))

    config = Config.load(config_path)

    assert config.api_endpoint == "https://vetscribe.example.com/api/soap"
    assert config.api_timeout_seconds == 45
    assert config.hotkey == "<ctrl>+<alt>+v"
