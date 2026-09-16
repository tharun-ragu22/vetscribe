from dataclasses import replace
from unittest.mock import MagicMock

from vetscribe.api_client import ApiClient
from vetscribe.audio_recorder import AudioRecorder
from vetscribe.avimark_injector import AvimarkInjector
from vetscribe.config import Config
from vetscribe.main import build_app
from vetscribe.pipeline import PipelineState


def test_build_app_wires_pipeline_dependencies_from_config():
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
        api_key="secret-token",
        target_window_matcher="PracticeSoft",
    )
    tk_root = MagicMock()

    tray_app, hotkey_listener, returned_root = build_app(config=config, tk_root=tk_root)

    pipeline = tray_app.pipeline
    assert isinstance(pipeline.recorder, AudioRecorder)
    assert isinstance(pipeline.api_client, ApiClient)
    assert pipeline.api_client.endpoint == "https://example.test/soap"
    assert pipeline.api_client.timeout_seconds == 15
    assert pipeline.api_client.api_key == "secret-token"
    assert isinstance(pipeline.injector, AvimarkInjector)
    assert pipeline.injector.title_marker == "PracticeSoft"
    assert returned_root is tk_root
    tk_root.withdraw.assert_called_once()


def test_tray_icon_turns_yellow_while_backend_call_is_in_flight():
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, _, _ = build_app(config=config, tk_root=tk_root)
    pipeline = tray_app.pipeline
    pipeline.recorder = MagicMock(save_wav=lambda path: path.write_bytes(b"wav"))
    pipeline.injector = MagicMock(inject=MagicMock(return_value=True))

    observed_color_mid_call = {}

    def fake_generate_soap_note(_audio_bytes):
        observed_color_mid_call["value"] = tray_app.icon.icon.getpixel(
            (tray_app.icon.icon.width // 2, tray_app.icon.icon.height // 2)
        )
        raise AssertionError("stop before real network/injection work")

    pipeline.api_client = MagicMock(generate_soap_note=fake_generate_soap_note)
    pipeline.state = PipelineState.RECORDING

    try:
        pipeline.toggle_recording()
    except AssertionError:
        pass

    assert observed_color_mid_call["value"][:3] == (255, 255, 0)


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


def test_build_app_error_callback_shows_flyout_with_error_message(mocker):
    mock_flyout_cls = mocker.patch("vetscribe.main.FlyoutWindow")
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, _, _ = build_app(config=config, tk_root=tk_root)
    pipeline = tray_app.pipeline

    pipeline.on_error("SOAP Generation Failed: backend unreachable.")

    mock_flyout_cls.assert_called_once()
    _, kwargs = mock_flyout_cls.call_args
    assert kwargs["master"] is tk_root
    assert kwargs["soap_text"] == "SOAP Generation Failed: backend unreachable."


def test_open_last_note_shows_flyout_with_last_soap_text(mocker):
    mock_flyout_cls = mocker.patch("vetscribe.main.FlyoutWindow")
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, _, _ = build_app(config=config, tk_root=tk_root)
    tray_app.pipeline.last_soap_text = "SUBJECTIVE: last note"

    tray_app.open_last_note()

    mock_flyout_cls.assert_called_once()
    _, kwargs = mock_flyout_cls.call_args
    assert kwargs["master"] is tk_root
    assert kwargs["soap_text"] == "SUBJECTIVE: last note"


def test_open_settings_opens_settings_window_with_current_config(mocker):
    mock_settings_cls = mocker.patch("vetscribe.main.SettingsWindow")
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, _, _ = build_app(config=config, tk_root=tk_root)
    tray_app.open_settings()

    mock_settings_cls.assert_called_once()
    _, kwargs = mock_settings_cls.call_args
    assert kwargs["master"] is tk_root
    assert kwargs["config"] is config


def test_saving_settings_persists_config_and_updates_live_components(mocker, tmp_path):
    mock_settings_cls = mocker.patch("vetscribe.main.SettingsWindow")
    mocker.patch("vetscribe.main.autostart")
    mocker.patch("vetscribe.hotkey_listener.keyboard.Listener")
    config_path = tmp_path / "config.json"
    mocker.patch("vetscribe.main.CONFIG_PATH", config_path)
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
        api_key="old-key",
        target_window_matcher="AVImark",
    )
    tk_root = MagicMock()

    tray_app, hotkey_listener, _ = build_app(config=config, tk_root=tk_root)
    hotkey_listener.start()
    tray_app.open_settings()

    _, kwargs = mock_settings_cls.call_args
    apply_settings = kwargs["on_save"]

    new_config = Config(
        api_endpoint="https://new.example.test/soap",
        api_timeout_seconds=45,
        hotkey="<ctrl>+<alt>+v",
        api_key="new-key",
        target_window_matcher="PracticeSoft",
    )
    apply_settings(new_config)

    pipeline = tray_app.pipeline
    assert pipeline.api_client.endpoint == "https://new.example.test/soap"
    assert pipeline.api_client.timeout_seconds == 45
    assert pipeline.api_client.api_key == "new-key"
    assert pipeline.injector.title_marker == "PracticeSoft"
    assert hotkey_listener.hotkey == "<ctrl>+<alt>+v"

    reloaded = Config.load(config_path)
    assert reloaded.api_endpoint == "https://new.example.test/soap"
    assert reloaded.hotkey == "<ctrl>+<alt>+v"


def test_saving_settings_enables_autostart_when_launch_on_startup_checked(mocker, tmp_path):
    mock_settings_cls = mocker.patch("vetscribe.main.SettingsWindow")
    mock_enable = mocker.patch("vetscribe.main.autostart.enable")
    mock_disable = mocker.patch("vetscribe.main.autostart.disable")
    mocker.patch("vetscribe.hotkey_listener.keyboard.Listener")
    mocker.patch("vetscribe.main.CONFIG_PATH", tmp_path / "config.json")
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, hotkey_listener, _ = build_app(config=config, tk_root=tk_root)
    hotkey_listener.start()
    tray_app.open_settings()
    apply_settings = mock_settings_cls.call_args.kwargs["on_save"]

    apply_settings(replace(config, launch_on_startup=True))
    mock_enable.assert_called_once()
    mock_disable.assert_not_called()

    apply_settings(replace(config, launch_on_startup=False))
    mock_disable.assert_called_once()


def test_build_app_wires_offline_queue_into_pipeline_and_tray_app():
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, _, _ = build_app(config=config, tk_root=tk_root)

    assert tray_app.offline_queue is tray_app.pipeline.offline_queue
    assert tray_app.offline_queue.api_client is tray_app.pipeline.api_client


def test_build_app_offline_queue_on_note_ready_shows_flyout(mocker):
    mock_flyout_cls = mocker.patch("vetscribe.main.FlyoutWindow")
    config = Config(
        api_endpoint="https://example.test/soap",
        api_timeout_seconds=15,
        hotkey="<ctrl>+<shift>+r",
    )
    tk_root = MagicMock()

    tray_app, _, _ = build_app(config=config, tk_root=tk_root)
    tray_app.offline_queue.on_note_ready("SUBJECTIVE: recovered note")

    mock_flyout_cls.assert_called_once()
    _, kwargs = mock_flyout_cls.call_args
    assert kwargs["master"] is tk_root
    assert kwargs["soap_text"] == "SUBJECTIVE: recovered note"
