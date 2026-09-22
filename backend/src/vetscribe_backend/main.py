import os
from pathlib import Path

import uvicorn

from vetscribe_backend.app import create_app
from vetscribe_backend.store import JsonFileExamStore

# Durable exam history so records survive restarts and sync across devices.
# Override the location with VETSCRIBE_EXAMS_PATH; defaults to the shared data root.
_EXAMS_PATH = Path(
    os.environ.get("VETSCRIBE_EXAMS_PATH", Path.home() / ".vetscribe" / "exams.json")
)

app = create_app(store=JsonFileExamStore(_EXAMS_PATH))


def run():
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8443")))


if __name__ == "__main__":
    run()
