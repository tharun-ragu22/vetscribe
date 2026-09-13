from vetscribe.hotkey_listener import HotkeyListener


def test_start_registers_ctrl_shift_r_hotkey_and_starts_listener(mocker):
    mock_global_hotkeys_cls = mocker.patch(
        "vetscribe.hotkey_listener.keyboard.GlobalHotKeys"
    )
    mock_listener = mock_global_hotkeys_cls.return_value

    listener = HotkeyListener(on_trigger=lambda: None)
    listener.start()

    args, kwargs = mock_global_hotkeys_cls.call_args
    hotkey_map = args[0] if args else kwargs["hotkey_map"]
    assert "<ctrl>+<shift>+r" in hotkey_map
    mock_listener.start.assert_called_once()
