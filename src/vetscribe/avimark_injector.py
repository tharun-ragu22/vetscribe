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
        # The specific AVImark window the vet was working in when the flyout
        # appeared. focus_and_inject pastes into this exact window so that,
        # with several patient charts open, the note lands in the right one.
        self.target_hwnd = None

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

    def find_avimark_windows(self):
        """Return the hwnds of every visible top-level AVImark window.

        Matches the same configured title marker as ``is_avimark_foreground``.
        Ordered as ``EnumWindows`` yields them, i.e. top-most in the Z-order
        first.
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
        return matches

    def find_avimark_window(self):
        """Return one visible top-level AVImark window (top-most), or None."""
        matches = self.find_avimark_windows()
        return matches[0] if matches else None

    def remember_active_window(self):
        """Record the currently-foreground AVImark window as the paste target.

        Called just before a flyout / history window is shown, while the vet's
        AVImark chart is still in front, to seed the target for the common case
        where they inject without navigating away. ``track_active_window`` then
        keeps it current. If the foreground isn't an AVImark window (e.g.
        History was opened from the tray menu), the target is cleared and
        injection falls back to auto-detection. Best-effort: a failing Win32
        call must never break showing the flyout.
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
        except Exception:
            self.target_hwnd = None
            return
        if self.title_marker.lower() in title.lower():
            self.target_hwnd = hwnd
            logger.debug("remembered active AVImark window %s (%r)", hwnd, title)
        else:
            self.target_hwnd = None

    def track_active_window(self):
        """Follow the vet to whichever AVImark chart they switch to.

        Polled on a timer while a flyout / history window is open. If an AVImark
        window is currently in front, it becomes the paste target; otherwise
        (our own flyout is in front, another app, etc.) the last AVImark target
        is left untouched -- so Copy & Inject lands in the chart the vet was
        *most recently* in, following their latest navigation. Best-effort.
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
        except Exception:
            return
        if self.title_marker.lower() in title.lower():
            self.target_hwnd = hwnd

    def _remembered_target(self):
        """The remembered AVImark window if it's still open and still AVImark."""
        hwnd = self.target_hwnd
        if hwnd is None:
            return None
        try:
            if not win32gui.IsWindow(hwnd):
                return None
            title = win32gui.GetWindowText(hwnd)
        except Exception:
            return None
        if self.title_marker.lower() not in title.lower():
            return None
        return hwnd

    def focus_and_inject(self, text: str) -> bool:
        """Bring AVImark to the foreground ourselves, then paste into it.

        This is the path for the flyout / history "Copy & Inject" buttons: the
        vet clicks our window, so AVImark is *not* the foreground window and the
        plain ``inject`` guard would (correctly) refuse. Here we actively locate
        the AVImark window, raise it, and only paste once we've confirmed it's
        genuinely the foreground window -- so the note still can't land in the
        wrong application. Whatever field the caret was last in inside AVImark is
        where the paste goes; we can't target a specific field.

        We prefer the exact window recorded by ``remember_active_window`` (the
        chart the vet was in). If that's unavailable and several AVImark windows
        are open, we can't tell which patient is meant, so we refuse to paste
        and leave the note on the clipboard for a manual Ctrl+V rather than risk
        the wrong chart.
        """
        hwnd = self._remembered_target()
        if hwnd is None:
            matches = self.find_avimark_windows()
            if not matches:
                logger.warning("injection skipped: no AVImark window found")
                return False
            if len(matches) > 1:
                logger.warning(
                    "injection skipped: %d AVImark windows open and none was "
                    "recorded as the active chart; note copied to clipboard for "
                    "manual paste",
                    len(matches),
                )
                self.copy_to_clipboard(text)
                return False
            hwnd = matches[0]
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
