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


def test_start_uses_custom_hotkey_passed_at_construction(mocker):
    mock_global_hotkeys_cls = mocker.patch(
        "vetscribe.hotkey_listener.keyboard.GlobalHotKeys"
    )

    listener = HotkeyListener(on_trigger=lambda: None, hotkey="<ctrl>+<alt>+v")
    listener.start()

    args, kwargs = mock_global_hotkeys_cls.call_args
    hotkey_map = args[0] if args else kwargs["hotkey_map"]
    assert "<ctrl>+<alt>+v" in hotkey_map
    assert "<ctrl>+<shift>+r" not in hotkey_map


def test_update_hotkey_while_running_stops_old_listener_and_starts_new_binding(mocker):
    mock_global_hotkeys_cls = mocker.patch(
        "vetscribe.hotkey_listener.keyboard.GlobalHotKeys"
    )
    first_listener = mock_global_hotkeys_cls.return_value

    listener = HotkeyListener(on_trigger=lambda: None)
    listener.start()

    second_listener = mocker.Mock()
    mock_global_hotkeys_cls.return_value = second_listener

    listener.update_hotkey("<ctrl>+<alt>+v")

    first_listener.stop.assert_called_once()
    args, kwargs = mock_global_hotkeys_cls.call_args
    hotkey_map = args[0] if args else kwargs["hotkey_map"]
    assert "<ctrl>+<alt>+v" in hotkey_map
    second_listener.start.assert_called_once()
    assert listener.hotkey == "<ctrl>+<alt>+v"


def test_update_hotkey_when_not_started_only_updates_pending_hotkey(mocker):
    mock_global_hotkeys_cls = mocker.patch(
        "vetscribe.hotkey_listener.keyboard.GlobalHotKeys"
    )

    listener = HotkeyListener(on_trigger=lambda: None)
    listener.update_hotkey("<ctrl>+<alt>+v")

    mock_global_hotkeys_cls.assert_not_called()
    assert listener.hotkey == "<ctrl>+<alt>+v"

    listener.start()

    args, kwargs = mock_global_hotkeys_cls.call_args
    hotkey_map = args[0] if args else kwargs["hotkey_map"]
    assert "<ctrl>+<alt>+v" in hotkey_map


def test_handle_trigger_invokes_on_trigger_callback():
    calls = []
    listener = HotkeyListener(on_trigger=lambda: calls.append("triggered"))

    listener._handle_trigger()

    assert calls == ["triggered"]


def test_handle_trigger_ignores_rapid_repeat_within_debounce_window(mocker):
    calls = []
    listener = HotkeyListener(on_trigger=lambda: calls.append("triggered"))
    times = iter([100.0, 100.05, 100.1])
    mocker.patch("vetscribe.hotkey_listener.time.monotonic", side_effect=lambda: next(times))

    listener._handle_trigger()
    listener._handle_trigger()
    listener._handle_trigger()

    assert calls == ["triggered"]


def test_handle_trigger_allows_trigger_after_debounce_window_elapses(mocker):
    calls = []
    listener = HotkeyListener(on_trigger=lambda: calls.append("triggered"))
    times = iter([100.0, 100.5])
    mocker.patch("vetscribe.hotkey_listener.time.monotonic", side_effect=lambda: next(times))

    listener._handle_trigger()
    listener._handle_trigger()

    assert calls == ["triggered", "triggered"]


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
