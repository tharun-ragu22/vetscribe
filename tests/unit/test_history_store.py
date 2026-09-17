from vetscribe.api_client import SoapNote
from vetscribe.history_store import HistoryStore


def make_note(subjective="sub", transcript="owner reports vomiting"):
    return SoapNote(
        subjective=subjective,
        objective="obj",
        assessment="assess",
        plan="plan",
        transcript=transcript,
    )


def test_save_then_list_round_trips_note_fields_and_transcript(tmp_path):
    store = HistoryStore(history_dir=tmp_path)

    store.save(make_note(subjective="Annual checkup", transcript="the dog is well"))

    entries = store.list_entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.subjective == "Annual checkup"
    assert entry.objective == "obj"
    assert entry.assessment == "assess"
    assert entry.plan == "plan"
    assert entry.transcript == "the dog is well"


def test_list_entries_returns_newest_first(tmp_path):
    store = HistoryStore(history_dir=tmp_path)

    store.save(make_note(subjective="first"))
    store.save(make_note(subjective="second"))
    store.save(make_note(subjective="third"))

    subjectives = [entry.subjective for entry in store.list_entries()]
    assert subjectives == ["third", "second", "first"]


def test_entry_exposes_formatted_soap_text_for_copy_and_inject(tmp_path):
    store = HistoryStore(history_dir=tmp_path)

    store.save(make_note(subjective="Annual checkup"))

    entry = store.list_entries()[0]
    assert "SUBJECTIVE: Annual checkup" in entry.soap_text
    assert "OBJECTIVE: obj" in entry.soap_text
    assert "ASSESSMENT: assess" in entry.soap_text
    assert "PLAN: plan" in entry.soap_text


def test_entry_records_a_timestamp(tmp_path):
    store = HistoryStore(history_dir=tmp_path)

    store.save(make_note())

    assert store.list_entries()[0].timestamp is not None


def test_list_entries_is_empty_when_no_notes_saved(tmp_path):
    store = HistoryStore(history_dir=tmp_path / "does-not-exist-yet")

    assert store.list_entries() == []


def test_list_entries_skips_unreadable_history_data(tmp_path):
    # A garbage file in the history directory must not crash the listing --
    # a corrupt entry is worse than a missing one, but neither should take
    # down the whole history view.
    store = HistoryStore(history_dir=tmp_path)
    store.save(make_note(subjective="good entry"))

    (tmp_path / "note_corrupt.json").write_text("this is not valid json {")

    subjectives = [entry.subjective for entry in store.list_entries()]
    assert subjectives == ["good entry"]
