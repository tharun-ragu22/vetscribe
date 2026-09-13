from unittest.mock import MagicMock

from vetscribe.pipeline import PipelineState
from vetscribe.tray_app import TrayApp, build_icon_image


def test_build_icon_image_returns_image_of_requested_color():
    image = build_icon_image("green")

    center_pixel = image.getpixel((image.width // 2, image.height // 2))
    assert center_pixel[:3] == (0, 128, 0)


def make_tray_app(**overrides):
    pipeline = MagicMock(state=PipelineState.IDLE)
    pipeline.configure_mock(**overrides)
    return TrayApp(pipeline=pipeline), pipeline


def test_update_icon_for_state_sets_icon_matching_recording_state():
    tray_app, pipeline = make_tray_app(state=PipelineState.RECORDING)

    tray_app.update_icon_for_state()

    center_pixel = tray_app.icon.icon.getpixel(
        (tray_app.icon.icon.width // 2, tray_app.icon.icon.height // 2)
    )
    assert center_pixel[:3] == (255, 0, 0)


def test_on_hotkey_triggered_toggles_pipeline_and_refreshes_icon():
    tray_app, pipeline = make_tray_app(state=PipelineState.IDLE)

    def fake_toggle():
        pipeline.state = PipelineState.RECORDING

    pipeline.toggle_recording.side_effect = fake_toggle

    tray_app.on_hotkey_triggered()

    pipeline.toggle_recording.assert_called_once()
    center_pixel = tray_app.icon.icon.getpixel(
        (tray_app.icon.icon.width // 2, tray_app.icon.icon.height // 2)
    )
    assert center_pixel[:3] == (255, 0, 0)


def test_menu_has_status_open_note_settings_separator_and_quit_items():
    tray_app, _pipeline = make_tray_app(state=PipelineState.IDLE)

    labels = [str(item) for item in tray_app.icon.menu.items]

    assert labels[0].startswith("Status:")
    assert labels[1] == "Open Last SOAP Note"
    assert labels[2] == "Settings"
    assert labels[4] == "Quit"


def test_status_menu_item_reflects_current_pipeline_state():
    tray_app, pipeline = make_tray_app(state=PipelineState.RECORDING)

    status_item = tray_app.icon.menu.items[0]

    assert status_item.text == "Status: Recording"
    assert status_item.enabled is False


def test_open_last_note_menu_item_disabled_when_no_note_yet():
    tray_app, pipeline = make_tray_app(state=PipelineState.IDLE, last_soap_text=None)

    open_note_item = tray_app.icon.menu.items[1]

    assert open_note_item.enabled is False


def test_open_last_note_invokes_on_show_note_with_last_soap_text():
    shown = []
    tray_app, pipeline = make_tray_app(state=PipelineState.IDLE, last_soap_text="SUBJECTIVE: text")
    tray_app.on_show_note = shown.append

    open_note_item = tray_app.icon.menu.items[1]
    assert open_note_item.enabled is True

    tray_app.open_last_note()

    assert shown == ["SUBJECTIVE: text"]


def test_open_settings_invokes_on_open_settings_callback():
    calls = []
    tray_app, _pipeline = make_tray_app(state=PipelineState.IDLE)
    tray_app.on_open_settings = lambda: calls.append("opened")

    tray_app.open_settings()

    assert calls == ["opened"]


def test_quit_stops_hotkey_listener_stops_active_recording_and_stops_icon():
    tray_app, pipeline = make_tray_app(state=PipelineState.RECORDING)
    hotkey_listener = MagicMock()
    tray_app.attach_hotkey_listener(hotkey_listener)
    tray_app.icon.stop = MagicMock()

    tray_app.quit()

    hotkey_listener.stop.assert_called_once()
    pipeline.recorder.stop.assert_called_once()
    tray_app.icon.stop.assert_called_once()


def test_quit_does_not_stop_recorder_when_not_recording():
    tray_app, pipeline = make_tray_app(state=PipelineState.IDLE)
    tray_app.icon.stop = MagicMock()

    tray_app.quit()

    pipeline.recorder.stop.assert_not_called()
    tray_app.icon.stop.assert_called_once()
