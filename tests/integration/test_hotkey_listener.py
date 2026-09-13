import threading
import time

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


def test_handle_trigger_invokes_on_trigger_callback():
    calls = []
    listener = HotkeyListener(on_trigger=lambda: calls.append("triggered"))

    listener._handle_trigger()

    assert calls == ["triggered"]


def test_handle_trigger_serializes_concurrent_calls_across_threads():
    max_concurrent = 0
    current_concurrent = 0
    guard = threading.Lock()

    def slow_on_trigger():
        nonlocal max_concurrent, current_concurrent
        with guard:
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
        time.sleep(0.05)
        with guard:
            current_concurrent -= 1

    listener = HotkeyListener(on_trigger=slow_on_trigger)
    threads = [
        threading.Thread(target=listener._handle_trigger) for _ in range(5)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert max_concurrent == 1
