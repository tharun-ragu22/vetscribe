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

    def find_avimark_window(self):
        """Return the hwnd of a visible top-level AVImark window, or None.

        Matches the same configured title marker as ``is_avimark_foreground``.
        """
        matches = []

        def _collect(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.title_marker.lower() in title.lower():
                    results.append(hwnd)
            # Return True so enumeration continues to every top-level window;
            # pywin32 stops the walk the moment the callback returns falsy.
            return True

        win32gui.EnumWindows(_collect, matches)
        return matches[0] if matches else None

    def focus_and_inject(self, text: str) -> bool:
        """Bring AVImark to the foreground ourselves, then paste into it.

        This is the path for the flyout / history "Copy & Inject" buttons: the
        vet clicks our window, so AVImark is *not* the foreground window and the
        plain ``inject`` guard would (correctly) refuse. Here we actively locate
        the AVImark window by title, raise it, and only paste once we've
        confirmed it's genuinely the foreground window -- so the note still can't
        land in the wrong application. Whatever field the caret was last in
        inside AVImark is where the paste goes; we can't target a specific field.
        """
        hwnd = self.find_avimark_window()
        if hwnd is None:
            logger.warning("injection skipped: no AVImark window found")
            return False
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        if not self.is_avimark_foreground():
            logger.warning(
                "injection skipped: could not bring AVImark to the foreground"
            )
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
