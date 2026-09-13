from unittest.mock import MagicMock

from vetscribe.api_client import SoapNote
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


def test_toggle_recording_from_recording_stops_and_injects_successfully():
    soap_note = SoapNote(
        subjective="sub", objective="obj", assessment="assess", plan="plan"
    )
    recorder = MagicMock(
        save_wav=MagicMock(side_effect=lambda path: path.write_bytes(b"fake-wav"))
    )
    deps_overrides = dict(
        recorder=recorder,
        api_client=MagicMock(generate_soap_note=MagicMock(return_value=soap_note)),
        injector=MagicMock(inject=MagicMock(return_value=True)),
    )
    pipeline, deps = make_pipeline(**deps_overrides)
    pipeline.state = PipelineState.RECORDING

    pipeline.toggle_recording()

    deps["recorder"].stop.assert_called_once()
    deps["recorder"].save_wav.assert_called_once()
    deps["api_client"].generate_soap_note.assert_called_once()
    deps["injector"].inject.assert_called_once()
    deps["on_flyout_needed"].assert_not_called()
    assert pipeline.state == PipelineState.IDLE


def test_toggle_recording_from_recording_calls_flyout_when_injection_fails():
    soap_note = SoapNote(
        subjective="sub", objective="obj", assessment="assess", plan="plan"
    )
    recorder = MagicMock(
        save_wav=MagicMock(side_effect=lambda path: path.write_bytes(b"fake-wav"))
    )
    deps_overrides = dict(
        recorder=recorder,
        api_client=MagicMock(generate_soap_note=MagicMock(return_value=soap_note)),
        injector=MagicMock(inject=MagicMock(return_value=False)),
    )
    pipeline, deps = make_pipeline(**deps_overrides)
    pipeline.state = PipelineState.RECORDING

    pipeline.toggle_recording()

    deps["on_flyout_needed"].assert_called_once()
    called_text = deps["on_flyout_needed"].call_args[0][0]
    assert "SUBJECTIVE: sub" in called_text
    assert "PLAN: plan" in called_text
    assert pipeline.state == PipelineState.IDLE


def test_toggle_recording_is_noop_while_processing():
    pipeline, deps = make_pipeline()
    pipeline.state = PipelineState.PROCESSING

    pipeline.toggle_recording()

    deps["recorder"].start.assert_not_called()
    deps["recorder"].stop.assert_not_called()
    assert pipeline.state == PipelineState.PROCESSING
