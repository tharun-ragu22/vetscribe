import itertools
import json
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from vetscribe.paths import get_appdata_base_dir
from vetscribe.pipeline import format_soap_text

logger = logging.getLogger("vetscribe.history_store")


def get_history_dir() -> Path:
    return get_appdata_base_dir() / "history"


def _now_ns() -> int:
    # Wrapped so tests can simulate a coarse clock; time.time_ns() is
    # high-resolution on all supported platforms, unlike datetime.now() whose
    # resolution is coarse on Windows.
    return time.time_ns()


@dataclass
class HistoryEntry:
    timestamp: str
    subjective: str
    objective: str
    assessment: str
    plan: str
    transcript: str
    entry_id: str = ""
    # When the vet edits a note, we can't reliably re-parse free-form text back
    # into the four structured fields, so the edited note is stored verbatim
    # here and takes precedence over the generated formatting.
    edited_soap_text: str = ""

    @property
    def soap_text(self) -> str:
        if self.edited_soap_text:
            return self.edited_soap_text
        return format_soap_text(self)


class HistoryStore:
    def __init__(self, history_dir=None):
        self.history_dir = Path(history_dir) if history_dir else get_history_dir()
        # Strictly increasing within the process, so notes saved in the same
        # clock tick still sort in insertion order (see entry_id below). Shared
        # across the pipeline and offline-queue threads via the one store
        # instance; next() is atomic under the GIL.
        self._sequence = itertools.count()

    def save(self, soap_note) -> HistoryEntry:
        self.history_dir.mkdir(parents=True, exist_ok=True)
        # Newest-first ordering is by filename, so the id must sort in creation
        # order: a high-resolution timestamp (orders across process restarts)
        # then a per-process counter (breaks ties when the clock is too coarse
        # to distinguish rapid saves -- e.g. datetime/now resolution on
        # Windows), then a random suffix purely for uniqueness.
        entry_id = (
            f"note_{_now_ns():019d}_{next(self._sequence):09d}_{uuid.uuid4().hex[:8]}"
        )
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "subjective": soap_note.subjective,
            "objective": soap_note.objective,
            "assessment": soap_note.assessment,
            "plan": soap_note.plan,
            "transcript": getattr(soap_note, "transcript", ""),
            "edited_soap_text": "",
        }
        self._path_for(entry_id).write_text(json.dumps(payload))
        logger.info("saved SOAP note to history: %s", entry_id)
        return self._entry_from_data(payload, entry_id)

    def update(self, entry_id, *, soap_text, transcript) -> "HistoryEntry | None":
        path = self._path_for(entry_id)
        if not path.exists():
            logger.warning("cannot update unknown history entry: %s", entry_id)
            return None
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            logger.warning("cannot update unreadable history file %s: %s", path, exc)
            return None
        data["edited_soap_text"] = soap_text
        data["transcript"] = transcript
        path.write_text(json.dumps(data))
        logger.info("updated SOAP note in history: %s", entry_id)
        return self._entry_from_data(data, entry_id)

    def delete(self, entry_id) -> bool:
        # The note and its transcript share one file, so unlinking it removes
        # both. Returns whether anything was actually deleted.
        path = self._path_for(entry_id)
        if not path.exists():
            logger.warning("cannot delete unknown history entry: %s", entry_id)
            return False
        path.unlink()
        logger.info("deleted SOAP note from history: %s", entry_id)
        return True

    def list_entries(self):
        if not self.history_dir.exists():
            return []
        entries = []
        for path in self.history_dir.glob("note_*.json"):
            try:
                data = json.loads(path.read_text())
                entries.append(self._entry_from_data(data, path.stem))
            except (OSError, ValueError, KeyError) as exc:
                logger.warning("skipping unreadable history file %s: %s", path, exc)
        # Newest first, by the recorded timestamp rather than the filename: a
        # past change to the id format means legacy filenames sort lexically
        # above current ones, which would push freshly recorded notes to the
        # bottom. The ISO timestamp orders correctly across both formats; the
        # entry_id breaks ties between notes saved within the same second (its
        # embedded sub-second counter preserves insertion order).
        entries.sort(key=lambda entry: (entry.timestamp, entry.entry_id), reverse=True)
        return entries

    def _path_for(self, entry_id) -> Path:
        return self.history_dir / f"{entry_id}.json"

    @staticmethod
    def _entry_from_data(data, entry_id) -> HistoryEntry:
        return HistoryEntry(
            timestamp=data["timestamp"],
            subjective=data["subjective"],
            objective=data["objective"],
            assessment=data["assessment"],
            plan=data["plan"],
            transcript=data.get("transcript", ""),
            entry_id=entry_id,
            edited_soap_text=data.get("edited_soap_text", ""),
        )
