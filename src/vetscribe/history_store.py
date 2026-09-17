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

    @property
    def soap_text(self) -> str:
        return format_soap_text(self)


class HistoryStore:
    def __init__(self, history_dir=None):
        self.history_dir = Path(history_dir) if history_dir else get_history_dir()

    def save(self, soap_note) -> HistoryEntry:
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            subjective=soap_note.subjective,
            objective=soap_note.objective,
            assessment=soap_note.assessment,
            plan=soap_note.plan,
            transcript=getattr(soap_note, "transcript", ""),
        )
        self.history_dir.mkdir(parents=True, exist_ok=True)
        # A microsecond timestamp plus a short random suffix keeps filenames
        # unique even if two notes are saved in the same instant (the live
        # pipeline and the offline-queue retry run on separate threads).
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.history_dir / f"note_{stamp}_{uuid.uuid4().hex[:8]}.json"
        path.write_text(json.dumps(entry.__dict__))
        logger.info("saved SOAP note to history: %s", path)
        return entry

    def list_entries(self):
        if not self.history_dir.exists():
            return []
        entries = []
        # Filenames embed a microsecond timestamp, so sorting by name puts the
        # newest note first even when several share the same display timestamp.
        for path in sorted(self.history_dir.glob("note_*.json"), reverse=True):
            try:
                data = json.loads(path.read_text())
                entries.append(
                    HistoryEntry(
                        timestamp=data["timestamp"],
                        subjective=data["subjective"],
                        objective=data["objective"],
                        assessment=data["assessment"],
                        plan=data["plan"],
                        transcript=data.get("transcript", ""),
                    )
                )
            except (OSError, ValueError, KeyError) as exc:
                logger.warning("skipping unreadable history file %s: %s", path, exc)
        return entries
