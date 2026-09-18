import tkinter as tk

from vetscribe import ui_strings

DEFAULT_WIDTH = 360
DEFAULT_HEIGHT = 320
DEFAULT_MARGIN = 20


class FlyoutWindow(tk.Toplevel):
    def __init__(
        self,
        master,
        soap_text,
        on_copy_and_inject,
        on_copy_to_clipboard,
        on_open_history=None,
    ):
        super().__init__(master)
        self.attributes("-topmost", True)
        work_left, work_top, work_right, work_bottom = self.screen_work_area()
        self.geometry(
            self.bottom_right_geometry(
                work_left=work_left,
                work_top=work_top,
                work_right=work_right,
                work_bottom=work_bottom,
                width=DEFAULT_WIDTH,
                height=DEFAULT_HEIGHT,
                margin=DEFAULT_MARGIN,
            )
        )

        # Pack the controls at the bottom *first* so they always reserve their
        # space; the note text then fills whatever's left. Otherwise the
        # full-height Text widget pushes the buttons past the window's bottom
        # edge and they're never seen (which hid "Open History" entirely).
        controls = tk.Frame(self)
        controls.pack(side="bottom", fill="x")

        button_row = tk.Frame(controls)
        button_row.pack(side="bottom")
        self.copy_and_inject_button = tk.Button(
            button_row,
            text=ui_strings.BUTTON_COPY_AND_INJECT,
            command=on_copy_and_inject,
        )
        self.copy_and_inject_button.pack(side="left")

        self.copy_to_clipboard_button = tk.Button(
            button_row,
            text=ui_strings.BUTTON_COPY_SOAP_NOTE,
            command=on_copy_to_clipboard,
        )
        self.copy_to_clipboard_button.pack(side="left")

        # Only offered when there's a note to browse -- error-message flyouts
        # pass no callback and omit the button entirely. Sits on the same row as
        # the copy/inject buttons.
        self.open_history_button = None
        if on_open_history is not None:
            self.open_history_button = tk.Button(
                button_row,
                text=ui_strings.BUTTON_OPEN_HISTORY,
                command=on_open_history,
            )
            self.open_history_button.pack(side="left")

        self.text_widget = tk.Text(self)
        self.text_widget.insert("1.0", soap_text)
        self.text_widget.pack(side="top", fill="both", expand=True)

        self.update()

    def screen_work_area(self):
        """Usable screen rectangle (left, top, right, bottom) as pixel coords.

        On Windows this excludes the taskbar via SPI_GETWORKAREA -- otherwise
        the flyout, anchored to the raw screen height, drops its bottom edge
        (and the buttons) behind the taskbar where they're clipped. Anywhere the
        query is unavailable (Linux dev/CI, headless), fall back to the full
        screen so behaviour is unchanged there.
        """
        try:
            import ctypes
            from ctypes import wintypes

            SPI_GETWORKAREA = 0x0030
            rect = wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
            ):
                return rect.left, rect.top, rect.right, rect.bottom
        except (AttributeError, OSError):
            pass
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    @staticmethod
    def bottom_right_geometry(
        work_left, work_top, work_right, work_bottom, width, height, margin
    ):
        x = work_right - width - margin
        y = work_bottom - height - margin
        # Keep the window on-screen horizontally if it's wider than the work
        # area. Vertically we deliberately don't clamp to the top edge: if the
        # note is taller than the usable area the bottom (the controls) must
        # stay visible, so we let the top run off instead.
        x = max(work_left, x)
        return f"{width}x{height}+{x}+{y}"
