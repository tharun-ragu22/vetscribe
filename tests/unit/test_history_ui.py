import tkinter

import pytest

from vetscribe.history_store import HistoryEntry
from vetscribe.history_ui import HistoryWindow


@pytest.fixture
def tk_root():
    root = tkinter.Tk()
    root.withdraw()
    yield root
    root.destroy()


def make_entry(subjective="sub", transcript="the owner reports vomiting"):
    return HistoryEntry(
        timestamp="2026-09-17T10:30:00",
        subjective=subjective,
        objective="obj",
        assessment="assess",
        plan="plan",
        transcript=transcript,
    )


def make_window(tk_root, entries, **overrides):
    kwargs = dict(
        master=tk_root,
        entries=entries,
        on_copy_and_inject=lambda soap_text: None,
        on_copy_to_clipboard=lambda soap_text: None,
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
