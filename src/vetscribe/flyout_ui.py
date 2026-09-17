import tkinter as tk

from vetscribe import ui_strings

DEFAULT_WIDTH = 360
DEFAULT_HEIGHT = 320
DEFAULT_MARGIN = 20


class FlyoutWindow(tk.Toplevel):
    def __init__(self, master, soap_text, on_copy_and_inject, on_copy_to_clipboard):
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

        self.text_widget = tk.Text(self)
        self.text_widget.insert("1.0", soap_text)
        self.text_widget.pack()

        self.copy_and_inject_button = tk.Button(
            self, text=ui_strings.BUTTON_COPY_AND_INJECT, command=on_copy_and_inject
        )
        self.copy_and_inject_button.pack()

        self.copy_to_clipboard_button = tk.Button(
            self, text=ui_strings.BUTTON_COPY_SOAP_NOTE, command=on_copy_to_clipboard
        )
        self.copy_to_clipboard_button.pack()
        self.update()

    @staticmethod
    def bottom_right_geometry(screen_width, screen_height, width, height, margin):
        x = screen_width - width - margin
        y = screen_height - height - margin
        return f"{width}x{height}+{x}+{y}"
