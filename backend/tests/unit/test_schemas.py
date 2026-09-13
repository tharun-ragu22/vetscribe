from vetscribe_backend.schemas import SoapNote


def test_soap_note_to_dict_returns_all_four_fields():
    note = SoapNote(subjective="s", objective="o", assessment="a", plan="p")
    assert note.to_dict() == {"subjective": "s", "objective": "o", "assessment": "a", "plan": "p"}
