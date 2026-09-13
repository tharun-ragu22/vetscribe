import pytest

from vetscribe_backend.note_generation.parsing import NoteParsingError, parse_soap_json


def test_parse_soap_json_parses_plain_json():
    note = parse_soap_json(
        '{"subjective": "s", "objective": "o", "assessment": "a", "plan": "p"}'
    )
    assert note.subjective == "s"
    assert note.plan == "p"


def test_parse_soap_json_strips_markdown_code_fences():
    note = parse_soap_json(
        '```json\n{"subjective": "s", "objective": "o", "assessment": "a", "plan": "p"}\n```'
    )
    assert note.plan == "p"


def test_parse_soap_json_raises_on_invalid_json():
    with pytest.raises(NoteParsingError):
        parse_soap_json("not json")


def test_parse_soap_json_raises_on_missing_field():
    with pytest.raises(NoteParsingError, match="objective"):
        parse_soap_json('{"subjective": "s"}')
