from vetscribe.avimark_injector import AvimarkInjector


def test_is_avimark_foreground_returns_true_when_title_contains_avimark(mocker):
    mock_win32gui = mocker.patch("vetscribe.avimark_injector.win32gui")
    mock_win32gui.GetForegroundWindow.return_value = 12345
    mock_win32gui.GetWindowText.return_value = "AVImark - [Patient: Max (Golden Retriever)]"

    injector = AvimarkInjector()

    assert injector.is_avimark_foreground() is True
    mock_win32gui.GetWindowText.assert_called_once_with(12345)


def test_is_avimark_foreground_returns_false_for_other_windows(mocker):
    mock_win32gui = mocker.patch("vetscribe.avimark_injector.win32gui")
    mock_win32gui.GetForegroundWindow.return_value = 999
    mock_win32gui.GetWindowText.return_value = "Notepad"

    injector = AvimarkInjector()

    assert injector.is_avimark_foreground() is False


def test_copy_to_clipboard_opens_empties_sets_and_closes_clipboard(mocker):
    mock_win32clipboard = mocker.patch("vetscribe.avimark_injector.win32clipboard")

    injector = AvimarkInjector()
    injector.copy_to_clipboard("SUBJECTIVE: patient is doing well.")

    mock_win32clipboard.OpenClipboard.assert_called_once_with()
    mock_win32clipboard.EmptyClipboard.assert_called_once_with()
    mock_win32clipboard.SetClipboardText.assert_called_once_with(
        "SUBJECTIVE: patient is doing well.", mock_win32clipboard.CF_UNICODETEXT
    )
    mock_win32clipboard.CloseClipboard.assert_called_once_with()
