from tests.acceptance.mock_avimark import WINDOW_TITLE, MockAvimarkWindow


def test_mock_avimark_window_has_expected_title_and_focused_text_widget():
    window = MockAvimarkWindow()
    try:
        window.update()
        assert window.title() == WINDOW_TITLE
        assert window.title() == "AVImark - [Patient: Max (Golden Retriever)]"
        assert window.focus_get() is window.text_widget
    finally:
        window.destroy()
