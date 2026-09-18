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
        self.geometry(
            self.bottom_right_geometry(
                screen_width=self.winfo_screenwidth(),
                screen_height=self.winfo_screenheight(),
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

        # The pre-computed geometry above is only a first guess: the real window
        # manager decorates and may resize the window, so its actual rendered
        # height can exceed DEFAULT_HEIGHT and push the bottom edge (the buttons)
        # off the screen. Re-anchor using the window's *measured* size, and do it
        # again on the event loop once the WM has finished mapping it, so the
        # bottom is always visible without the user having to drag it up.
        self._anchor_bottom_right()
        self.after(0, self._anchor_bottom_right)

    def _anchor_bottom_right(self):
        self.update_idletasks()
        x, y = self.fit_bottom_right(
            screen_width=self.winfo_screenwidth(),
            screen_height=self.winfo_screenheight(),
            width=self.winfo_width(),
            height=self.winfo_height(),
            margin=DEFAULT_MARGIN,
        )
        self.geometry(f"+{x}+{y}")

    @staticmethod
    def fit_bottom_right(screen_width, screen_height, width, height, margin):
        """Bottom-right position that keeps the *whole* window on-screen.

        Anchors to the bottom-right corner but never lets the left/top edge go
        past ``margin``, so a window taller or wider than the screen still shows
        its bottom-right (where the buttons live) rather than running off-edge.
        """
        x = max(margin, screen_width - width - margin)
        y = max(margin, screen_height - height - margin)
        return x, y

    @staticmethod
    def bottom_right_geometry(screen_width, screen_height, width, height, margin):
        x, y = FlyoutWindow.fit_bottom_right(
            screen_width, screen_height, width, height, margin
        )
        return f"{width}x{height}+{x}+{y}"
