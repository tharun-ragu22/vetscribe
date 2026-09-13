import enum
import tempfile
from pathlib import Path


class PipelineState(enum.Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"


def format_soap_text(soap_note) -> str:
    return (
        f"SUBJECTIVE: {soap_note.subjective}\n"
        f"OBJECTIVE: {soap_note.objective}\n"
        f"ASSESSMENT: {soap_note.assessment}\n"
        f"PLAN: {soap_note.plan}"
    )


class Pipeline:
    def __init__(self, recorder, api_client, injector, on_flyout_needed):
        self.recorder = recorder
        self.api_client = api_client
        self.injector = injector
        self.on_flyout_needed = on_flyout_needed
        self.state = PipelineState.IDLE

    def toggle_recording(self):
        if self.state == PipelineState.IDLE:
            self.recorder.start()
            self.state = PipelineState.RECORDING
        elif self.state == PipelineState.RECORDING:
            self._stop_and_process()

    def _stop_and_process(self):
        self.state = PipelineState.PROCESSING
        self.recorder.stop()

        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = Path(tmp_dir) / "recording.wav"
            self.recorder.save_wav(wav_path)
            audio_bytes = wav_path.read_bytes()

        soap_note = self.api_client.generate_soap_note(audio_bytes)
        soap_text = format_soap_text(soap_note)

        injected = self.injector.inject(soap_text)
        if not injected:
            self.on_flyout_needed(soap_text)

        self.state = PipelineState.IDLE
