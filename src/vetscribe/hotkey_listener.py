import threading

from pynput import keyboard

HOTKEY = "<ctrl>+<shift>+r"


class HotkeyListener:
    def __init__(self, on_trigger):
        self.on_trigger = on_trigger
        self._lock = threading.Lock()
        self._listener = None

    def start(self):
        self._listener = keyboard.GlobalHotKeys({HOTKEY: self._handle_trigger})
        self._listener.start()

    def stop(self):
        if self._listener is not None:
            self._listener.stop()

    def _handle_trigger(self):
        with self._lock:
            self.on_trigger()
