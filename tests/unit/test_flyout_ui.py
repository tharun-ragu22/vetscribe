import tkinter

import pytest

from vetscribe import ui_strings
from vetscribe.flyout_ui import DEFAULT_HEIGHT, DEFAULT_WIDTH, FlyoutWindow


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


def test_copy_and_inject_button_has_expected_label_and_invokes_callback(tk_root):
    calls = []
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="text",
        on_copy_and_inject=lambda: calls.append("inject"),
        on_copy_to_clipboard=lambda: None,
    )

    assert flyout.copy_and_inject_button["text"] == ui_strings.BUTTON_COPY_AND_INJECT
    flyout.copy_and_inject_button.invoke()
    assert calls == ["inject"]


def test_copy_to_clipboard_button_has_expected_label_and_invokes_callback(tk_root):
    calls = []
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="text",
        on_copy_and_inject=lambda: None,
        on_copy_to_clipboard=lambda: calls.append("copy"),
    )

    assert flyout.copy_to_clipboard_button["text"] == ui_strings.BUTTON_COPY_SOAP_NOTE
    flyout.copy_to_clipboard_button.invoke()
    assert calls == ["copy"]


def test_open_history_button_invokes_callback_when_provided(tk_root):
    calls = []
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="text",
        on_copy_and_inject=lambda: None,
        on_copy_to_clipboard=lambda: None,
        on_open_history=lambda: calls.append("history"),
    )

    assert flyout.open_history_button["text"] == ui_strings.BUTTON_OPEN_HISTORY
    flyout.open_history_button.invoke()
    assert calls == ["history"]


def test_button_row_is_pinned_to_the_bottom_so_a_tall_note_cant_hide_it(
    tk_root,
):
    # Regression: the note Text used to be packed first with no size limit, so a
    # long note pushed the buttons below the window's bottom edge and out of
    # sight. The controls must stay pinned to the bottom while the note fills the
    # space above them. Open History shares the button row, packed alongside the
    # copy/inject buttons.
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="line\n" * 200,
        on_copy_and_inject=lambda: None,
        on_copy_to_clipboard=lambda: None,
        on_open_history=lambda: None,
    )

    text_info = flyout.text_widget.pack_info()
    assert text_info["side"] == "top"
    assert str(text_info["expand"]) in ("1", "True")
    assert text_info["fill"] == "both"
    button_row = flyout.open_history_button.master
    assert button_row.pack_info()["side"] == "bottom"
    assert flyout.open_history_button.pack_info()["side"] == "left"


def test_open_history_button_is_absent_when_no_callback_is_given(tk_root):
    # Error-message flyouts have no note to browse, so they omit the button.
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="text",
        on_copy_and_inject=lambda: None,
        on_copy_to_clipboard=lambda: None,
    )

    assert flyout.open_history_button is None


def test_flyout_window_is_topmost(tk_root):
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="text",
        on_copy_and_inject=lambda: None,
        on_copy_to_clipboard=lambda: None,
    )

    assert flyout.attributes("-topmost") == 1


def test_long_note_does_not_grow_the_window_past_the_requested_size(tk_root):
    # Regression: the Text widget's default 24-line height made the toplevel
    # grow taller than DEFAULT_HEIGHT, so its bottom edge (the buttons) landed
    # below the screen and the flyout looked cut off. The window must keep the
    # requested size regardless of note length; the note scrolls inside it.
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="line\n" * 500,
        on_copy_and_inject=lambda: None,
        on_copy_to_clipboard=lambda: None,
        on_open_history=lambda: None,
    )
    flyout.update_idletasks()

    size = flyout.geometry().split("+")[0]
    assert size == f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}"


def test_bottom_right_geometry_places_window_in_bottom_right_corner_with_margin():
    geometry = FlyoutWindow.bottom_right_geometry(
        screen_width=1920, screen_height=1080, width=400, height=300, margin=20
    )

    assert geometry == "400x300+1500+760"
