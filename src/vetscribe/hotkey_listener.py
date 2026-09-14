import logging
import threading
import time

from pynput import keyboard

logger = logging.getLogger("vetscribe.hotkey_listener")

HOTKEY = "<ctrl>+<shift>+r"

# GlobalHotKeys re-fires its callback on every OS key-repeat event while the
# combo is held down, not just once per physical press. Without this, holding
# the hotkey for even a fraction of a second causes several rapid
# start/stop toggles against a single key press, sending near-empty audio to
# the backend. Debounce so repeats within this window are ignored.
DEBOUNCE_SECONDS = 0.3


class HotkeyListener:
    def __init__(self, on_trigger, hotkey=HOTKEY):
        self.on_trigger = on_trigger
        self.hotkey = hotkey
        self._lock = threading.Lock()
        self._listener = None
        self._last_trigger_time = None

    def start(self):
        self._listener = keyboard.GlobalHotKeys({self.hotkey: self._handle_trigger})
        self._listener.start()
        logger.info("listening for hotkey %s", self.hotkey)

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
            now = time.monotonic()
            if (
                self._last_trigger_time is not None
                and now - self._last_trigger_time < DEBOUNCE_SECONDS
            ):
                logger.debug("hotkey %s trigger ignored (debounced)", self.hotkey)
                return
            self._last_trigger_time = now
            logger.info("hotkey %s triggered", self.hotkey)
            self.on_trigger()
