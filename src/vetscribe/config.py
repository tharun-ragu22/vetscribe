import json
from dataclasses import dataclass

DEFAULT_CONFIG = {
    "api_endpoint": "https://localhost:8443/api/soap",
    "api_timeout_seconds": 30,
    "hotkey": "<ctrl>+<shift>+r",
}


@dataclass
class Config:
    api_endpoint: str
    api_timeout_seconds: int
    hotkey: str

    @classmethod
    def load(cls, path):
        if not path.exists():
            return cls(**DEFAULT_CONFIG)
        values = json.loads(path.read_text())
        return cls(**values)
