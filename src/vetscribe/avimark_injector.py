import win32gui

AVIMARK_TITLE_MARKER = "AVImark"


class AvimarkInjector:
    def is_avimark_foreground(self) -> bool:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        return AVIMARK_TITLE_MARKER.lower() in title.lower()
