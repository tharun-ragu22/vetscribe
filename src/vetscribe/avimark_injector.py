import win32clipboard
import win32gui

AVIMARK_TITLE_MARKER = "AVImark"


class AvimarkInjector:
    def is_avimark_foreground(self) -> bool:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        return AVIMARK_TITLE_MARKER.lower() in title.lower()

    def copy_to_clipboard(self, text: str):
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()
