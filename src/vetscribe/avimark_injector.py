import logging

import win32api
import win32clipboard
import win32con
import win32gui

AVIMARK_TITLE_MARKER = "AVImark"

logger = logging.getLogger("vetscribe.avimark_injector")


class AvimarkInjector:
    def __init__(self, title_marker: str = AVIMARK_TITLE_MARKER):
        self.title_marker = title_marker

    def is_avimark_foreground(self) -> bool:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        logger.debug("foreground window title: %r", title)
        return self.title_marker.lower() in title.lower()

    def copy_to_clipboard(self, text: str):
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()

    def inject(self, text: str) -> bool:
        if not self.is_avimark_foreground():
            logger.warning("injection skipped: AVImark is not the foreground window")
            return False
        self.copy_to_clipboard(text)
        self._send_ctrl_v()
        logger.info("SOAP note injected into AVImark")
        return True

    def _send_ctrl_v(self):
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
