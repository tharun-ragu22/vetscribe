from unittest.mock import MagicMock

from vetscribe.pipeline import Pipeline, PipelineState


def make_pipeline(**overrides):
    defaults = dict(
        recorder=MagicMock(),
        api_client=MagicMock(),
        injector=MagicMock(),
        on_flyout_needed=MagicMock(),
    )
    defaults.update(overrides)
    return Pipeline(**defaults), defaults


def test_toggle_recording_from_idle_starts_recording():
    pipeline, deps = make_pipeline()

    pipeline.toggle_recording()

    deps["recorder"].start.assert_called_once()
    assert pipeline.state == PipelineState.RECORDING
