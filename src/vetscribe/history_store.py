import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from vetscribe.paths import get_appdata_base_dir
from vetscribe.pipeline import format_soap_text

logger = logging.getLogger("vetscribe.history_store")


def get_history_dir() -> Path:
    return get_appdata_base_dir() / "history"


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

    def save(self, soap_note) -> HistoryEntry:
        self.history_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        # A microsecond timestamp plus a short random suffix keeps filenames
        # unique even if two notes are saved in the same instant (the live
        # pipeline and the offline-queue retry run on separate threads).
        entry_id = f"note_{now.strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:8]}"
        payload = {
            "timestamp": now.isoformat(timespec="seconds"),
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

    def list_entries(self):
        if not self.history_dir.exists():
            return []
        entries = []
        # Filenames embed a microsecond timestamp, so sorting by name puts the
        # newest note first even when several share the same display timestamp.
        for path in sorted(self.history_dir.glob("note_*.json"), reverse=True):
            try:
                data = json.loads(path.read_text())
                entries.append(self._entry_from_data(data, path.stem))
            except (OSError, ValueError, KeyError) as exc:
                logger.warning("skipping unreadable history file %s: %s", path, exc)
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
