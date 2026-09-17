from vetscribe_backend.schemas import SoapNote, SoapResult


def test_soap_note_to_dict_returns_all_four_fields():
    note = SoapNote(subjective="s", objective="o", assessment="a", plan="p")
    assert note.to_dict() == {"subjective": "s", "objective": "o", "assessment": "a", "plan": "p"}


def test_soap_result_to_dict_includes_note_fields_and_transcript():
    note = SoapNote(subjective="s", objective="o", assessment="a", plan="p")
    result = SoapResult(note=note, transcript="owner reports vomiting")
    assert result.to_dict() == {
        "subjective": "s",
        "objective": "o",
        "assessment": "a",
        "plan": "p",
        "transcript": "owner reports vomiting",
    }
