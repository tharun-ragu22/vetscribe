import threading

from pynput import keyboard

HOTKEY = "<ctrl>+<shift>+r"


class HotkeyListener:
    def __init__(self, on_trigger, hotkey=HOTKEY):
        self.on_trigger = on_trigger
        self.hotkey = hotkey
        self._lock = threading.Lock()
        self._listener = None

    def start(self):
        self._listener = keyboard.GlobalHotKeys({self.hotkey: self._handle_trigger})
        self._listener.start()

    def stop(self):
        if self._listener is not None:
            self._listener.stop()

    def update_hotkey(self, new_hotkey):
        was_running = self._listener is not None
        self.hotkey = new_hotkey
        if was_running:
            self.stop()
            self.start()

    def _handle_trigger(self):
        with self._lock:
            self.on_trigger()
