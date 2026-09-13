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


def test_mock_avimark_window_dumps_text_content_to_file_on_modification(tmp_path):
    dump_path = tmp_path / "dump.txt"
    window = MockAvimarkWindow(dump_path=dump_path)
    try:
        window.update()
        window.text_widget.insert("1.0", "SUBJECTIVE: patient text")
        window.update()

        assert dump_path.read_text() == "SUBJECTIVE: patient text"
    finally:
        window.destroy()
