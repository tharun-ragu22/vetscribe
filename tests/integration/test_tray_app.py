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
