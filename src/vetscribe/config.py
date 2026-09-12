import json
from dataclasses import asdict, dataclass

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
        values = {**DEFAULT_CONFIG, **json.loads(path.read_text())}
        return cls(**values)

    def save(self, path):
        path.write_text(json.dumps(asdict(self)))
