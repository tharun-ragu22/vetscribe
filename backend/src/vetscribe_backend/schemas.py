from dataclasses import asdict, dataclass


@dataclass
class SoapNote:
    subjective: str
    objective: str
    assessment: str
    plan: str

    def to_dict(self) -> dict:
        return asdict(self)
