import enum
import logging
import tempfile
from datetime import datetime
from pathlib import Path

from vetscribe.api_client import ApiClientError

logger = logging.getLogger("vetscribe.pipeline")


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
    def __init__(
        self,
        recorder,
        api_client,
        injector,
        on_flyout_needed,
        on_error=None,
        recordings_dir=None,
        offline_queue=None,
    ):
        self.recorder = recorder
        self.api_client = api_client
        self.injector = injector
        self.on_flyout_needed = on_flyout_needed
        self.on_error = on_error or (lambda message: None)
        self.recordings_dir = Path(recordings_dir) if recordings_dir else (
            Path.home() / ".vetscribe" / "recordings"
        )
        self.offline_queue = offline_queue
        self.state = PipelineState.IDLE
        self.last_soap_text = None

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

        try:
            soap_note = self.api_client.generate_soap_note(audio_bytes)
        except ApiClientError as exc:
            saved_path = self._save_failed_audio(audio_bytes)
            logger.error("SOAP generation failed: %s (audio saved to %s)", exc, saved_path)
            if self.offline_queue is not None:
                self.offline_queue.enqueue(audio_bytes)
            self.on_error(
                f"SOAP Generation Failed: {exc}. Raw audio saved locally to {saved_path}."
            )
            self.state = PipelineState.IDLE
            return

        soap_text = format_soap_text(soap_note)
        self.last_soap_text = soap_text
        logger.info("SOAP note generated successfully")

        injected = self.injector.inject(soap_text)
        logger.info("AVImark injection %s", "succeeded" if injected else "failed, showing flyout")
        if not injected:
            self.on_flyout_needed(soap_text)

        self.state = PipelineState.IDLE

    def _save_failed_audio(self, audio_bytes):
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.recordings_dir / f"failed_{timestamp}.wav"
        path.write_bytes(audio_bytes)
        return path
