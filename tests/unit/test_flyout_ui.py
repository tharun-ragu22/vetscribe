import tkinter

import pytest

from vetscribe.flyout_ui import FlyoutWindow


@pytest.fixture
def tk_root():
    root = tkinter.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_flyout_window_displays_soap_note_text(tk_root):
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="SUBJECTIVE: text\nOBJECTIVE: text\nASSESSMENT: text\nPLAN: text",
        on_copy_and_inject=lambda: None,
        on_copy_to_clipboard=lambda: None,
    )

    displayed_text = flyout.text_widget.get("1.0", "end-1c")

    assert "SUBJECTIVE: text" in displayed_text
    assert "PLAN: text" in displayed_text
