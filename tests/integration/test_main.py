from unittest.mock import MagicMock

from vetscribe.api_client import ApiClient
from vetscribe.audio_recorder import AudioRecorder
from vetscribe.avimark_injector import AvimarkInjector
from vetscribe.config import Config
from vetscribe.main import build_app


def test_build_app_wires_pipeline_dependencies_from_config():
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, hotkey_listener, returned_root = build_app(config=config, tk_root=tk_root)

    pipeline = tray_app.pipeline
    assert isinstance(pipeline.recorder, AudioRecorder)
    assert isinstance(pipeline.api_client, ApiClient)
    assert pipeline.api_client.endpoint == "https://example.test/soap"
    assert pipeline.api_client.timeout_seconds == 15
    assert isinstance(pipeline.injector, AvimarkInjector)
    assert returned_root is tk_root
    tk_root.withdraw.assert_called_once()


def test_build_app_wires_hotkey_listener_to_tray_app_trigger():
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, hotkey_listener, _ = build_app(config=config, tk_root=tk_root)

    assert hotkey_listener.on_trigger == tray_app.on_hotkey_triggered
    assert tray_app.hotkey_listener is hotkey_listener


def test_build_app_wires_configured_hotkey_into_hotkey_listener():
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<alt>+v",
    )
    tk_root = MagicMock()

    _tray_app, hotkey_listener, _ = build_app(config=config, tk_root=tk_root)

    assert hotkey_listener.hotkey == "<ctrl>+<alt>+v"


def test_build_app_flyout_callback_creates_flyout_window_on_injection_failure(mocker):
    mock_flyout_cls = mocker.patch("vetscribe.main.FlyoutWindow")
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, _, _ = build_app(config=config, tk_root=tk_root)
    pipeline = tray_app.pipeline

    pipeline.on_flyout_needed("SUBJECTIVE: text")

    mock_flyout_cls.assert_called_once()
    _, kwargs = mock_flyout_cls.call_args
    assert kwargs["master"] is tk_root
    assert kwargs["soap_text"] == "SUBJECTIVE: text"
