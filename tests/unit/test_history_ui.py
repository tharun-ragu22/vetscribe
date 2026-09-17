import tkinter
import uuid

import pytest

from vetscribe.history_store import HistoryEntry
from vetscribe.history_ui import HistoryWindow


@pytest.fixture
def tk_root():
    root = tkinter.Tk()
    root.withdraw()
    yield root
    root.destroy()


def make_entry(subjective="sub", transcript="the owner reports vomiting", entry_id=None):
    return HistoryEntry(
        timestamp="2026-09-17T10:30:00",
        subjective=subjective,
        objective="obj",
        assessment="assess",
        plan="plan",
        transcript=transcript,
        # Each entry needs a stable, unique id: the window preserves the vet's
        # selection across auto-refresh by matching on it.
        entry_id=entry_id or uuid.uuid4().hex,
    )


def make_window(tk_root, entries, **overrides):
    # Feed entries through a callable so the window can re-fetch them (that's how
    # auto-refresh works). Return a fresh copy each call so a test can mutate the
    # source list to simulate a note being saved while the window is open.
    kwargs = dict(
        master=tk_root,
        load_entries=lambda: list(entries),
        on_copy_and_inject=lambda soap_text: None,
        on_copy_to_clipboard=lambda soap_text: None,
        on_save_edit=lambda entry_id, soap_text, transcript: None,
        # Disable the timer-driven poll in tests; drive refresh() explicitly so
        # assertions are deterministic and no stray `after` jobs outlive the test.
        poll_interval_ms=None,
    )
    kwargs.update(overrides)
    return HistoryWindow(**kwargs)


def test_history_window_lists_one_row_per_entry(tk_root):
    entries = [make_entry(subjective="first"), make_entry(subjective="second")]

    window = make_window(tk_root, entries)

    rows = window.listbox.get(0, "end")
    assert len(rows) == 2
    assert any("first" in row for row in rows)
    assert any("second" in row for row in rows)


def test_selecting_an_entry_shows_its_note_and_transcript(tk_root):
    entries = [
        make_entry(subjective="Annual checkup", transcript="dog is well"),
        make_entry(subjective="Dental cleaning", transcript="tartar buildup noted"),
    ]
    window = make_window(tk_root, entries)

    window.show_entry(1)

    note_text = window.note_text.get("1.0", "end-1c")
    transcript_text = window.transcript_text.get("1.0", "end-1c")
    assert "SUBJECTIVE: Dental cleaning" in note_text
    assert "tartar buildup noted" in transcript_text


def test_window_shows_newest_entry_by_default(tk_root):
    # Entries arrive newest-first (as HistoryStore.list_entries returns them),
    # so the first entry should be shown without the user clicking anything.
    entries = [
        make_entry(subjective="Newest", transcript="latest transcript"),
        make_entry(subjective="Older", transcript="older transcript"),
    ]
    window = make_window(tk_root, entries)

    note_text = window.note_text.get("1.0", "end-1c")
    assert "SUBJECTIVE: Newest" in note_text


def test_copy_and_inject_button_sends_selected_entry_soap_text(tk_root):
    entries = [make_entry(subjective="Annual checkup")]
    injected = []
    window = make_window(
        tk_root, entries, on_copy_and_inject=injected.append
    )
    window.show_entry(0)

    assert window.copy_and_inject_button["text"] == "Copy & Inject to AVImark"
    window.copy_and_inject_button.invoke()

    assert len(injected) == 1
    assert "SUBJECTIVE: Annual checkup" in injected[0]


def test_copy_to_clipboard_button_sends_selected_entry_soap_text(tk_root):
    entries = [make_entry(subjective="Annual checkup")]
    copied = []
    window = make_window(
        tk_root, entries, on_copy_to_clipboard=copied.append
    )
    window.show_entry(0)

    assert window.copy_to_clipboard_button["text"] == "Copy to Clipboard"
    window.copy_to_clipboard_button.invoke()

    assert len(copied) == 1
    assert "SUBJECTIVE: Annual checkup" in copied[0]


def test_history_window_handles_empty_history_without_crashing(tk_root):
    window = make_window(tk_root, entries=[])

    assert window.listbox.get(0, "end") == ()
    # Copy/inject with nothing selected must be a safe no-op, not a crash.
    window.copy_to_clipboard_button.invoke()


def test_refresh_adds_newly_saved_note_and_shows_it_when_viewing_newest(tk_root):
    entries = [make_entry(subjective="First note", transcript="first")]
    window = make_window(tk_root, entries)  # auto-selects the newest on open

    # A new note is saved while the window is open (prepended -- newest first).
    entries.insert(0, make_entry(subjective="Brand new note", transcript="brand new"))
    window.refresh()

    rows = window.listbox.get(0, "end")
    assert len(rows) == 2
    assert any("Brand new note" in row for row in rows)
    # The vet was on the newest entry, so the just-recorded note is shown for them.
    assert "SUBJECTIVE: Brand new note" in window.note_text.get("1.0", "end-1c")
    assert "brand new" in window.transcript_text.get("1.0", "end-1c")


def test_refresh_preserves_a_deliberately_selected_older_note(tk_root):
    entries = [
        make_entry(subjective="Newest", transcript="newest"),
        make_entry(subjective="Older", transcript="older"),
    ]
    window = make_window(tk_root, entries)
    window.show_entry(1)  # the vet deliberately opens an older note

    entries.insert(0, make_entry(subjective="Just recorded", transcript="just recorded"))
    window.refresh()

    # The list grows, but the note the vet is reading is not yanked away.
    assert len(window.listbox.get(0, "end")) == 3
    assert "SUBJECTIVE: Older" in window.note_text.get("1.0", "end-1c")
    assert "older" in window.transcript_text.get("1.0", "end-1c")


def test_refresh_populates_from_empty_when_first_note_arrives(tk_root):
    entries = []
    window = make_window(tk_root, entries)
    assert window.listbox.get(0, "end") == ()

    entries.append(make_entry(subjective="First ever", transcript="first ever"))
    window.refresh()

    assert len(window.listbox.get(0, "end")) == 1
    assert "SUBJECTIVE: First ever" in window.note_text.get("1.0", "end-1c")


def test_refresh_is_a_noop_when_nothing_changed(tk_root):
    entries = [
        make_entry(subjective="Newest", transcript="newest"),
        make_entry(subjective="Older", transcript="older"),
    ]
    window = make_window(tk_root, entries)
    window.show_entry(1)

    window.refresh()  # store unchanged

    # Selection is undisturbed and the list is unchanged.
    assert len(window.listbox.get(0, "end")) == 2
    assert "SUBJECTIVE: Older" in window.note_text.get("1.0", "end-1c")


def test_editing_and_saving_sends_the_edited_text_to_the_save_callback(tk_root):
    saved = []
    entry = make_entry(subjective="Annual checkup", transcript="orig", entry_id="n1")
    window = make_window(
        tk_root,
        [entry],
        on_save_edit=lambda entry_id, soap_text, transcript: saved.append(
            (entry_id, soap_text, transcript)
        ),
    )
    window.show_entry(0)

    # The vet edits both panes, then saves.
    window.note_text.delete("1.0", "end")
    window.note_text.insert("1.0", "SUBJECTIVE: corrected note")
    window.transcript_text.delete("1.0", "end")
    window.transcript_text.insert("1.0", "corrected transcript")
    window.save_button.invoke()

    assert saved == [("n1", "SUBJECTIVE: corrected note", "corrected transcript")]


def test_auto_refresh_does_not_discard_an_in_progress_unsaved_edit(tk_root):
    entries = [make_entry(subjective="Only note", transcript="orig", entry_id="n1")]
    window = make_window(tk_root, entries)
    window.show_entry(0)

    # The vet starts editing but has not saved yet...
    window.note_text.delete("1.0", "end")
    window.note_text.insert("1.0", "half-typed edit")

    # ...and a new note is recorded, triggering an auto-refresh.
    entries.insert(0, make_entry(subjective="Just recorded", transcript="new", entry_id="n2"))
    window.refresh()

    # The new note shows up in the list, but the unsaved edit is NOT clobbered.
    assert len(window.listbox.get(0, "end")) == 2
    assert window.note_text.get("1.0", "end-1c") == "half-typed edit"
