import os
import sys
from pathlib import Path


def get_appdata_base_dir() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "VetScribe"
    return Path.home() / ".vetscribe"
