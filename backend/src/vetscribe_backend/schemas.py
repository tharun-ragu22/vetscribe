from dataclasses import asdict, dataclass


@dataclass
class SoapNote:
    subjective: str
    objective: str
    assessment: str
    plan: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SoapResult:
    note: SoapNote
    transcript: str

    def to_dict(self) -> dict:
        return {**self.note.to_dict(), "transcript": self.transcript}
