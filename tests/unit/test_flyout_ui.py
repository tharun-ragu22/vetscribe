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


def test_copy_and_inject_button_has_expected_label_and_invokes_callback(tk_root):
    calls = []
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="text",
        on_copy_and_inject=lambda: calls.append("inject"),
        on_copy_to_clipboard=lambda: None,
    )

    assert flyout.copy_and_inject_button["text"] == "Copy & Inject to AVImark"
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

    assert flyout.copy_to_clipboard_button["text"] == "Copy to Clipboard"
    flyout.copy_to_clipboard_button.invoke()
    assert calls == ["copy"]


def test_flyout_window_is_topmost(tk_root):
    flyout = FlyoutWindow(
        master=tk_root,
        soap_text="text",
        on_copy_and_inject=lambda: None,
        on_copy_to_clipboard=lambda: None,
    )

    assert flyout.attributes("-topmost") == 1


def test_bottom_right_geometry_places_window_in_bottom_right_corner_with_margin():
    geometry = FlyoutWindow.bottom_right_geometry(
        screen_width=1920, screen_height=1080, width=400, height=300, margin=20
    )

    assert geometry == "400x300+1500+760"
