import logging
import threading
from datetime import datetime
from pathlib import Path

from vetscribe.api_client import ApiClientError
from vetscribe.paths import get_appdata_base_dir
from vetscribe.pipeline import format_soap_text

logger = logging.getLogger("vetscribe.offline_queue")


def get_queue_dir() -> Path:
    return get_appdata_base_dir() / "queue"


class OfflineQueue:
    def __init__(self, api_client, on_note_ready, queue_dir=None, poll_interval_seconds=60):
        self.api_client = api_client
        self.on_note_ready = on_note_ready
        self.queue_dir = Path(queue_dir) if queue_dir else get_queue_dir()
        self.poll_interval_seconds = poll_interval_seconds
        self._stop_event = threading.Event()
        self._thread = None

    def enqueue(self, audio_bytes: bytes) -> Path:
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.queue_dir / f"queued_{timestamp}.wav"
        path.write_bytes(audio_bytes)
        logger.info("queued recording for retry: %s", path)
        return path

    def queued_files(self):
        if not self.queue_dir.exists():
            return []
        return sorted(self.queue_dir.glob("queued_*.wav"))

    def process_once(self):
        processed = []
        for path in self.queued_files():
            audio_bytes = path.read_bytes()
            try:
                soap_note = self.api_client.generate_soap_note(audio_bytes)
            except ApiClientError as exc:
                logger.info("backend still unavailable, will retry later: %s", exc)
                break
            path.unlink()
            logger.info("queued recording %s processed successfully", path)
            self.on_note_ready(format_soap_text(soap_note))
            processed.append(path)
        return processed

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop_event.wait(self.poll_interval_seconds):
            self.process_once()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
